import pytest

import laspy
from laspy.header import Version
from laspy.point.format import PointFormat
import numpy as np
import pyproj
from osgeo import gdal, osr

from densitycheck.density import ReturnKind

gdal.UseExceptions()
osr.UseExceptions()

@pytest.fixture()
def pyproj_crs():
     return pyproj.CRS("EPSG:7416")

@pytest.fixture()
def osr_spatialreference():
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(7416)
    return srs

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
def las_data(las_header, tile_ll, pyproj_crs):
     las_header.offsets = [600000.0, 6200000.0, 0.0]
     las_header.scales = [0.001, 0.001, 0.001]
     las_header.add_crs(pyproj_crs)

     las = laspy.LasData(header=las_header)
     las.xyz = tile_ll[np.newaxis, :] + np.array([
        [100.0, 900.0, 20.0],
        [600.0, 900.0, 30.0],
        [700.0, 800.0, 20.0],
        [800.0, 250.0, 10.0]
     ])

     las.return_number = np.array([1, 1, 2, 2])
     las.number_of_returns = np.array([1, 3, 3, 2])

     return las

@pytest.fixture()
def gdal_driver():
     return gdal.GetDriverByName('MEM')

@pytest.fixture()
def dataset(gdal_driver):
     gdal_driver.Create('point_density')

@pytest.fixture()
def expected_raster(return_kind):
     match return_kind:
          case ReturnKind.ALL:
               grid = np.array([[4e-6, 8e-6], [0, 4e-6]])
          case ReturnKind.FIRST:
               grid = np.array([[4e-6, 4e-6]])
          case ReturnKind.LAST:
               grid = np.array([[4e-6, 0], [0, 4e-6]])

     return grid

@pytest.fixture()
def input_filename(tmp_path, las_data):
     filename = tmp_path / "input.las"
     las_data.write(filename)
     return filename

@pytest.fixture()
def output_filename(tmp_path):
     filename = tmp_path / "output.tif"
     return filename
