import pytest

import laspy
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

@pytest.fixture()
def las_data(pointcloud_xyz, pyproj_crs):
     header = laspy.LasHeader(version="1.4", point_format=6)
     header.offsets = [600000.0, 6200000.0, 0.0]
     header.scales = [0.001, 0.001, 0.001]
     header.add_crs(pyproj_crs)
     las = laspy.LasData(header=header)
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
