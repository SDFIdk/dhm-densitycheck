import numpy as np
from osgeo import gdal, osr

from enum import Enum, auto

gdal.UseExceptions()
osr.UseExceptions()

NODATA_VALUE = -9999

class ReturnKind(Enum):
    ALL = auto()
    FIRST = auto()
    LAST = auto()

def get_density(las_data, cell_size, return_kind: ReturnKind, mask_layer=None):
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

    output_spatialreference = osr.SpatialReference()
    output_spatialreference.ImportFromWkt(input_crs.to_wkt())

    driver = gdal.GetDriverByName('MEM')

    if mask_layer is None:
        cell_areas = cell_area
    else:
        mask_dataset = driver.Create('mask_raster', num_cols, num_rows, 1, gdal.GDT_Float32)
        mask_dataset.SetGeoTransform(raster_geotransform)
        mask_dataset.SetProjection(output_spatialreference.ExportToWkt())
        mask_band = mask_dataset.GetRasterBand(1)
        mask_band.WriteArray(cell_area * np.ones((num_rows, num_cols)))
        gdal.RasterizeLayer(
            mask_dataset,
            [1], # band 1
            mask_layer,
            burn_values=[0],
            options=[
                'ALL_TOUCHED=TRUE',
            ]
        )
        cell_areas = mask_band.ReadAsArray()

    cell_point_counts = cell_point_counts_flat.reshape(num_rows, num_cols)
    with np.errstate(divide='ignore', invalid='ignore'):
        cell_densities = cell_point_counts / cell_areas
    cell_densities[~np.isfinite(cell_densities)] = NODATA_VALUE

    dataset = driver.Create('density_raster', num_cols, num_rows, 1, gdal.GDT_Float32)
    dataset.SetGeoTransform(raster_geotransform)
    dataset.SetProjection(output_spatialreference.ExportToWkt())
    band = dataset.GetRasterBand(1)
    band.SetNoDataValue(NODATA_VALUE)
    band.WriteArray(cell_densities)

    return dataset
