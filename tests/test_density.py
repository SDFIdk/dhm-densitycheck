from osgeo import osr
import numpy as np

from densitycheck.density import get_density, NODATA_VALUE

osr.UseExceptions()

def test_get_density(las_data, expected_raster, expected_stats, return_kind, osr_spatialreference, mask_datasrc_opt):
    if mask_datasrc_opt is None:
        mask_layer = None
    else:
        mask_layer = mask_datasrc_opt.GetLayer()

    density_result = get_density(las_data, 500.0, return_kind, mask_layer=mask_layer)
    dataset = density_result.dataset
    output_stats = density_result.stats

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

    assert output_stats.min == expected_stats.min
    assert output_stats.max == expected_stats.max
    assert output_stats.mean == expected_stats.mean
    assert output_stats.median == expected_stats.median
    assert output_stats.std == expected_stats.std
    assert output_stats.var == expected_stats.var
