import pytest

import laspy
from laspy.header import Version
from laspy.point.format import PointFormat
import numpy as np
import pyproj
from osgeo import gdal, osr

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
def pointcloud_xyz():
    offset = np.array([[600000.0, 6200000.0, 0.0]])
    coords = np.array([
        [100.0, 900.0, 20.0],
        [600.0, 900.0, 30.0],
        [700.0, 800.0, 20.0],
        [800.0, 250.0, 10.0]
        ])
    return offset + coords

@pytest.fixture(params=[
     (Version(1, 2), PointFormat(1)),
     (Version(1, 4), PointFormat(6)),
])
def las_header(request):
     version, point_format = request.param
     return laspy.LasHeader(version=version, point_format=point_format)

@pytest.fixture()
def las_data(las_header, pointcloud_xyz, pyproj_crs):
     las_header.offsets = [600000.0, 6200000.0, 0.0]
     las_header.scales = [0.001, 0.001, 0.001]
     las_header.add_crs(pyproj_crs)

     las = laspy.LasData(header=las_header)
     las.x = pointcloud_xyz[:,0]
     las.y = pointcloud_xyz[:,1]
     las.z = pointcloud_xyz[:,2]

     return las

@pytest.fixture()
def gdal_driver():
     return gdal.GetDriverByName('MEM')

@pytest.fixture()
def dataset(gdal_driver):
     gdal_driver.Create('point_density')
