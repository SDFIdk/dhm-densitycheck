import numpy as np
from osgeo import gdal, osr

from collections import namedtuple
from enum import Enum, auto

gdal.UseExceptions()
osr.UseExceptions()

NODATA_VALUE = -9999

class ReturnKind(Enum):
    ALL = auto()
    FIRST = auto()
    LAST = auto()

Stats = namedtuple('Stats', ['min', 'max', 'mean', 'median', 'std', 'var'])
DensityResult = namedtuple('DensityResult', ['dataset', 'stats'])

def get_density(las_data, cell_size, return_kind: ReturnKind, include_layer=None, exclude_layer=None):
    input_points = las_data.points

    input_crs = las_data.header.parse_crs()
    
    match return_kind:
        case ReturnKind.ALL:
            relevant_points = input_points
        case ReturnKind.FIRST:
            relevant_indices = input_points.return_number == 1
            relevant_points = input_points[relevant_indices]
        case ReturnKind.LAST:
            relevant_indices = input_points.return_number == input_points.number_of_returns
            relevant_points = input_points[relevant_indices]

    relevant_xy = np.column_stack([relevant_points.x, relevant_points.y])

    relevant_xy_int = (relevant_xy // cell_size).astype(int)
    
    x_int_min = min(relevant_xy_int[:,0])
    x_int_max = max(relevant_xy_int[:,0])
    y_int_min = min(relevant_xy_int[:,1])
    y_int_max = max(relevant_xy_int[:,1])

    raster_ul_x = cell_size * x_int_min
    raster_ul_y = cell_size * (y_int_max + 1)
    raster_geotransform = [raster_ul_x, cell_size, 0.0,
                           raster_ul_y, 0.0, -cell_size]
    
    relevant_rowcol = np.column_stack([y_int_max - relevant_xy_int[:,1], relevant_xy_int[:,0] - x_int_min])
    
    # Cast to "proper" int so GDAL doesn't complain
    num_rows = int(max(relevant_rowcol[:,0]) + 1)
    num_cols = int(max(relevant_rowcol[:,1]) + 1)
    
    relevant_flatindices = num_cols*relevant_rowcol[:,0] + relevant_rowcol[:,1]

    cell_point_counts_flat = np.zeros(num_rows*num_cols)

    # Unbuffered "add 1" at the relevant indices
    np.add.at(cell_point_counts_flat, relevant_flatindices, 1)

    cell_area = cell_size**2

    if input_crs is not None:
        output_spatialreference = osr.SpatialReference()
        output_spatialreference.ImportFromWkt(input_crs.to_wkt())

    driver = gdal.GetDriverByName('MEM')

    cell_areas = cell_area * np.ones((num_rows, num_cols))

    if include_layer is not None:
        include_dataset = driver.Create('include_raster', num_cols, num_rows, 1, gdal.GDT_Float32)
        include_dataset.SetGeoTransform(raster_geotransform)
        if input_crs is not None:
            include_dataset.SetProjection(output_spatialreference.ExportToWkt())
        include_band = include_dataset.GetRasterBand(1)
        include_band.WriteArray(np.zeros((num_rows, num_cols)))
        gdal.RasterizeLayer(
            include_dataset,
            [1], # band 1
            include_layer,
            burn_values=[1]
        )
        cell_areas *= include_band.ReadAsArray()

    if exclude_layer is not None:
        exclude_dataset = driver.Create('exclude_raster', num_cols, num_rows, 1, gdal.GDT_Float32)
        exclude_dataset.SetGeoTransform(raster_geotransform)
        if input_crs is not None:
            exclude_dataset.SetProjection(output_spatialreference.ExportToWkt())
        exclude_band = exclude_dataset.GetRasterBand(1)
        exclude_band.WriteArray(np.ones((num_rows, num_cols)))
        gdal.RasterizeLayer(
            exclude_dataset,
            [1], # band 1
            exclude_layer,
            burn_values=[0],
            options=[
                'ALL_TOUCHED=TRUE',
            ]
        )
        cell_areas *= exclude_band.ReadAsArray()

    cell_point_counts = cell_point_counts_flat.reshape(num_rows, num_cols)
    with np.errstate(divide='ignore', invalid='ignore'):
        cell_densities = cell_point_counts / cell_areas
    valid_densities_unrolled = cell_densities[np.isfinite(cell_densities)].reshape((-1,))
    cell_densities[~np.isfinite(cell_densities)] = NODATA_VALUE

    stat_min = np.min(valid_densities_unrolled)
    stat_max = np.max(valid_densities_unrolled)
    stat_median = np.median(valid_densities_unrolled)
    stat_mean = np.mean(valid_densities_unrolled)
    stat_std = np.std(valid_densities_unrolled)
    stat_var = np.var(valid_densities_unrolled)

    stats = Stats(min=stat_min, max=stat_max, mean=stat_mean, median=stat_median, std=stat_std, var=stat_var)

    dataset = driver.Create('density_raster', num_cols, num_rows, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(raster_geotransform)
    if input_crs is not None:
        dataset.SetProjection(output_spatialreference.ExportToWkt())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(NODATA_VALUE)
    band.WriteArray(cell_densities)

    result = DensityResult(dataset=dataset, stats=stats)
    return result
