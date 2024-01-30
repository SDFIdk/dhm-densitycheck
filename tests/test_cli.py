from osgeo import gdal, osr
import numpy as np

import subprocess

from densitycheck.density import NODATA_VALUE

gdal.UseExceptions()
osr.UseExceptions()

def call_point_density(args):
    subprocess.check_call(['point_density'] + args)

def test_cli_help():
    call_point_density(['-h'])

def test_cli_full(input_filename, output_filename, return_kind, expected_raster, osr_spatialreference):
    call_point_density([input_filename, output_filename, '--cell-size', '500.0', '--returns', return_kind.name])

    output_dataset = gdal.Open(output_filename)
    output_srs = osr.SpatialReference(output_dataset.GetProjection())
    output_geotransform = output_dataset.GetGeoTransform()
    output_band = output_dataset.GetRasterBand(1)
    output_nodata_value = output_band.GetNoDataValue()
    output_array = output_band.ReadAsArray()

    assert output_srs.IsSame(osr_spatialreference)
    np.testing.assert_allclose(output_geotransform, [600000.0, 500.0, 0.0, 6201000.0, 0.0, -500.0])
    assert (output_dataset.RasterYSize, output_dataset.RasterXSize) == expected_raster.shape
    assert output_nodata_value == NODATA_VALUE
    np.testing.assert_allclose(output_array, expected_raster)
