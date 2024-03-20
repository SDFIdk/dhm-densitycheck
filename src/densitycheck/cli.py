from osgeo import gdal, ogr
import laspy

from densitycheck.density import get_density, ReturnKind

import argparse

gdal.UseExceptions()
ogr.UseExceptions()

def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('input_las', type=str, help='path to input pointcloud file')
    argument_parser.add_argument('output_raster', type=str, help='path to desired output raster (COG)')
    argument_parser.add_argument('--cell-size', type=float, default=1.0, help='cell size in georeferenced units')
    argument_parser.add_argument('--returns', type=str, default='ALL', choices=[kind.name for kind in ReturnKind], help='return number of points to consider')
    argument_parser.add_argument('--exclude', type=str, default=None, help='path to exclusion mask (OGR-readable datasource)')

    input_arguments = argument_parser.parse_args()

    las_data = laspy.read(input_arguments.input_las)
    output_path = input_arguments.output_raster
    cell_size = input_arguments.cell_size
    return_kind = ReturnKind[input_arguments.returns]
    mask_path = input_arguments.exclude

    if mask_path is None:
        mask_layer = None
    else:
        mask_datasrc = ogr.Open(mask_path)
        mask_layer = mask_datasrc.GetLayer()

    output_driver = gdal.GetDriverByName('COG')
    temp_dataset = get_density(las_data, cell_size, return_kind, mask_layer=mask_layer)
    output_driver.CreateCopy(output_path, temp_dataset)
