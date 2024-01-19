from osgeo import osr
import numpy as np

osr.UseExceptions()

from densitycheck.density import get_density

def test_get_density(las_data, osr_spatialreference):
    dataset = get_density(las_data, 500.0)
    
    output_srs = osr.SpatialReference(dataset.GetProjection())
    output_geotransform = dataset.GetGeoTransform()
    output_array = dataset.GetRasterBand(1).ReadAsArray()

    assert output_srs.IsSame(osr_spatialreference)
    np.testing.assert_allclose(output_geotransform, [600000.0, 500.0, 0.0, 6201000.0, 0.0, -500.0])
    assert (dataset.RasterXSize, dataset.RasterYSize) == (2, 2)
    np.testing.assert_allclose(output_array, [[4e-6, 8e-6], [0, 4e-6]])
