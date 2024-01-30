from osgeo import gdal
import laspy

from densitycheck.density import get_density, ReturnKind

import argparse

gdal.UseExceptions()

def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('input_las', type=str, help='path to input pointcloud file')
    argument_parser.add_argument('output_raster', type=str, help='path to desired output raster (COG)')
    argument_parser.add_argument('--cell-size', type=float, default=1.0, help='cell size in georeferenced units')
    argument_parser.add_argument('--returns', type=str, default='ALL', choices=[kind.name for kind in ReturnKind], help='return number of points to consider')
    # TODO return number argument?

    input_arguments = argument_parser.parse_args()

    las_data = laspy.read(input_arguments.input_las)
    output_path = input_arguments.output_raster
    cell_size = input_arguments.cell_size
    return_kind = ReturnKind[input_arguments.returns]

    output_driver = gdal.GetDriverByName('COG')
    temp_dataset = get_density(las_data, cell_size, return_kind)
    output_driver.CreateCopy(output_path, temp_dataset)
