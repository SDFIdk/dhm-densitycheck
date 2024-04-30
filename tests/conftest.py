import pytest

import laspy
from laspy.header import Version
from laspy.point.format import PointFormat
import numpy as np
import pyproj
from osgeo import gdal, ogr, osr

from densitycheck.density import Stats, ReturnKind, NODATA_VALUE

gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

# Test with example data located roughly like this:
# Points:
# +-----+-----+
# | *   | * * |
# |     |     |
# +-----+-----+
# |     |  *  |
# |     |     |
# +-----+-----+
#
# Mask:
# +-----+-----+
# |     |   ##|
# |     |    #|
# +-----+-----+
# |#####|     |
# |#####|     |
# +-----+-----+

@pytest.fixture()
def pyproj_crs():
     return pyproj.CRS("EPSG:7416")

@pytest.fixture(params=[False, True])
def pyproj_crs_opt(request, pyproj_crs):
     if request.param:
          return pyproj_crs
     else:
          return None

@pytest.fixture()
def osr_spatialreference():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(7416)
    return srs

@pytest.fixture()
def osr_spatialreference_opt(osr_spatialreference, pyproj_crs_opt):
     if pyproj_crs_opt is None:
          return None
     else:
          return osr_spatialreference

@pytest.fixture()
def tile_ll():
     return np.array([600000.0, 6200000.0, 0.0])

@pytest.fixture(params=[kind for kind in ReturnKind])
def return_kind(request):
     return request.param

@pytest.fixture(params=[
     (Version(1, 2), PointFormat(1)),
     (Version(1, 4), PointFormat(6)),
])
def las_header(request):
     version, point_format = request.param
     return laspy.LasHeader(version=version, point_format=point_format)

@pytest.fixture()
def las_data(las_header, tile_ll, pyproj_crs_opt):
     las_header.offsets = [600000.0, 6200000.0, 0.0]
     las_header.scales = [0.001, 0.001, 0.001]
     if pyproj_crs_opt is not None:
          las_header.add_crs(pyproj_crs_opt)

     las = laspy.LasData(header=las_header)
     las.xyz = tile_ll[np.newaxis, :] + np.array([
        [100.0, 900.0, 20.0],
        [600.0, 600.0, 30.0],
        [900.0, 900.0, 20.0],
        [800.0, 250.0, 10.0]
     ])

     las.return_number = np.array([1, 1, 2, 2])
     las.number_of_returns = np.array([1, 3, 3, 2])

     return las

@pytest.fixture()
def include_datasrc(tile_ll, osr_spatialreference):
     driver = ogr.GetDriverByName('Memory')
     datasrc = driver.CreateDataSource('include')
     layer = datasrc.CreateLayer('include_polygons', osr_spatialreference, ogr.wkbPolygon)
     layer_defn = layer.GetLayerDefn()
     polygons_xyz = [
          # np.array([
          #      [500.0, 1500.0, 0.0],
          #      [500.0, 500.0, 0.0],
          #      [1500.0, 500.0, 0.0],
          #      [1500.0, 1500.0, 0.0],
          #      [500.0, 1500.0, 0.0],
          # ]),
          np.array([
               [0.0, 0.0, 0.0],
               [1000.0, 0.0, 0.0],
               [1000.0, 1000.0, 0.0],
               [0.0, 1000.0, 0.0],
               [0.0, 0.0, 0.0],
          ]),
     ]

     for polygon_xyz in polygons_xyz:
          feature = ogr.Feature(layer_defn)
          polygon = ogr.Geometry(ogr.wkbPolygon)
          ring = ogr.Geometry(ogr.wkbLinearRing)
          for xyz in polygon_xyz:
               full_xyz = xyz + tile_ll

               ring.AddPoint(*full_xyz)
          polygon.AddGeometry(ring)
          feature.SetGeometry(polygon)
          layer.CreateFeature(feature)

     return datasrc

@pytest.fixture(params=[False, True])
def include_datasrc_opt(request, include_datasrc):
     if request.param:
          return include_datasrc
     else:
          return None

@pytest.fixture()
def include_file(include_datasrc_opt, tmp_path):
     if include_datasrc_opt is None:
          return None
     else:
          output_driver = ogr.GetDriverByName('GPKG')
          output_path = tmp_path / "include.gpkg"
          output_driver.CopyDataSource(include_datasrc_opt, output_path)
          return str(output_path)

@pytest.fixture()
def exclude_datasrc(tile_ll, osr_spatialreference):
     driver = ogr.GetDriverByName('Memory')
     datasrc = driver.CreateDataSource('exclude')
     layer = datasrc.CreateLayer('exclude_polygons', osr_spatialreference, ogr.wkbPolygon)
     layer_defn = layer.GetLayerDefn()
     polygons_xyz = [
          np.array([
               [0.0, 0.0, 0.0],
               [500.0, 0.0, 0.0],
               [500.0, 500.0, 0.0],
               [0.0, 500.0, 0.0],
               [0.0, 0.0, 0.0],
          ]),
          np.array([
               [500.0, 1000.0, 0.0],
               [1000.0, 500.0, 0.0],
               [1000.0, 1000.0, 0.0],
               [500.0, 1000.0, 0.0],
          ])
     ]
     for polygon_xyz in polygons_xyz:
          feature = ogr.Feature(layer_defn)
          polygon = ogr.Geometry(ogr.wkbPolygon)
          ring = ogr.Geometry(ogr.wkbLinearRing)
          for xyz in polygon_xyz:
               full_xyz = xyz + tile_ll

               ring.AddPoint(*full_xyz)
          polygon.AddGeometry(ring)
          feature.SetGeometry(polygon)
          layer.CreateFeature(feature)

     return datasrc

@pytest.fixture(params=[False, True])
def exclude_datasrc_opt(request, exclude_datasrc):
     if request.param:
          return exclude_datasrc
     else:
          return None

@pytest.fixture()
def exclude_file(exclude_datasrc_opt, tmp_path):
     if exclude_datasrc_opt is None:
          return None
     else:
          output_driver = ogr.GetDriverByName('GPKG')
          output_path = tmp_path / "exclude.gpkg"
          output_driver.CopyDataSource(exclude_datasrc_opt, output_path)
          return str(output_path)

@pytest.fixture()
def gdal_driver():
     return gdal.GetDriverByName('MEM')

@pytest.fixture()
def dataset(gdal_driver):
     gdal_driver.Create('point_density')

@pytest.fixture()
def expected_raster(return_kind, exclude_datasrc_opt):
     if exclude_datasrc_opt is None:
          match return_kind:
               case ReturnKind.ALL:
                    grid = np.array([[4e-6, 8e-6], [0, 4e-6]])
               case ReturnKind.FIRST:
                    grid = np.array([[4e-6, 4e-6]])
               case ReturnKind.LAST:
                    grid = np.array([[4e-6, 0], [0, 4e-6]])
     else:
          match return_kind:
               case ReturnKind.ALL:
                    grid = np.array([[4e-6, NODATA_VALUE], [NODATA_VALUE, 4e-6]])
               case ReturnKind.FIRST:
                    grid = np.array([[4e-6, NODATA_VALUE]])
               case ReturnKind.LAST:
                    grid = np.array([[4e-6, NODATA_VALUE], [NODATA_VALUE, 4e-6]])

     return grid

@pytest.fixture()
def expected_stats(expected_raster):
     unrolled_raster = expected_raster.reshape((-1,))
     unrolled_raster_valid = unrolled_raster[unrolled_raster != NODATA_VALUE]

     stat_min = np.min(unrolled_raster_valid)
     stat_max = np.max(unrolled_raster_valid)
     stat_mean = np.mean(unrolled_raster_valid)
     stat_median = np.median(unrolled_raster_valid)
     stat_std = np.std(unrolled_raster_valid)
     stat_var = np.var(unrolled_raster_valid)

     stats = Stats(min=stat_min, max=stat_max, mean=stat_mean, median=stat_median, std=stat_std, var=stat_var)

     return stats

@pytest.fixture()
def input_filename(tmp_path, las_data):
     filename = tmp_path / "input.las"
     las_data.write(filename)
     return filename

@pytest.fixture()
def output_filename(tmp_path):
     filename = tmp_path / "output.tif"
     return filename
