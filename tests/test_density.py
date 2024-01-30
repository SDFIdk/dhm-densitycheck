from osgeo import osr
import numpy as np

from densitycheck.density import get_density, NODATA_VALUE

osr.UseExceptions()

def test_get_density(las_data, expected_raster, return_kind, osr_spatialreference):
    dataset = get_density(las_data, 500.0, return_kind)
    
    output_srs = osr.SpatialReference(dataset.GetProjection())
    output_geotransform = dataset.GetGeoTransform()
    output_band = dataset.GetRasterBand(1)
    output_nodata_value = output_band.GetNoDataValue()
    output_array = output_band.ReadAsArray()

    assert output_srs.IsSame(osr_spatialreference)
    np.testing.assert_allclose(output_geotransform, [600000.0, 500.0, 0.0, 6201000.0, 0.0, -500.0])
    assert (dataset.RasterYSize, dataset.RasterXSize) == expected_raster.shape
    assert output_nodata_value == NODATA_VALUE
    np.testing.assert_allclose(output_array, expected_raster)
