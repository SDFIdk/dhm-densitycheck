from osgeo import gdal
import laspy

from densitycheck.density import get_density

import argparse

gdal.UseExceptions()

def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('input_las', type=str, help='path to input pointcloud file')
    argument_parser.add_argument('output_raster', type=str, help='path to desired output raster (COG)')
    argument_parser.add_argument('--cell-size', type=float, default=1.0, help='cell size in georeferenced units')
    # TODO return number argument?

    input_arguments = argument_parser.parse_args()

    las_data = laspy.read(input_arguments.input_las)
    output_path = input_arguments.output_raster
    cell_size = input_arguments.cell_size

    output_driver = gdal.GetDriverByName('COG')
    temp_dataset = get_density(las_data, cell_size)
    output_driver.CreateCopy(output_path, temp_dataset)
