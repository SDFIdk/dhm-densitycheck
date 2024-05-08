from osgeo import gdal, ogr
import laspy
import pyproj

from densitycheck.density import get_density, ReturnKind

import argparse
from collections import OrderedDict
import json
from pathlib import Path
import sys

gdal.UseExceptions()
ogr.UseExceptions()

def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('input_las', type=str, help='path to input pointcloud file')
    argument_parser.add_argument('output_raster', type=str, help='path to desired output raster (COG)')
    argument_parser.add_argument('--cell-size', type=float, default=1.0, help='cell size in georeferenced units')
    argument_parser.add_argument('--returns', type=str, default='ALL', choices=[kind.name for kind in ReturnKind], help='return number of points to consider')
    argument_parser.add_argument('--include', type=str, default=None, help='path to inclusion mask (OGR-readable datasource)')
    argument_parser.add_argument('--exclude', type=str, default=None, help='path to exclusion mask (OGR-readable datasource)')
    argument_parser.add_argument('--print-stats', action='store_true', help='print cell statistics to stdout')

    input_arguments = argument_parser.parse_args()

    input_basename = Path(input_arguments.input_las).name
    las_data = laspy.read(input_arguments.input_las)
    output_path = input_arguments.output_raster
    cell_size = input_arguments.cell_size
    return_kind = ReturnKind[input_arguments.returns]
    include_mask_path = input_arguments.include
    exclude_mask_path = input_arguments.exclude
    do_print_stats = input_arguments.print_stats

    if include_mask_path is None:
        include_mask_layer = None
    else:
        include_mask_datasrc = ogr.Open(include_mask_path)
        include_mask_layer = include_mask_datasrc.GetLayer()

    if exclude_mask_path is None:
        exclude_mask_layer = None
    else:
        exclude_mask_datasrc = ogr.Open(exclude_mask_path)
        exclude_mask_layer = exclude_mask_datasrc.GetLayer()

    output_driver = gdal.GetDriverByName('COG')
    density_result = get_density(las_data, cell_size, return_kind, include_layer=include_mask_layer, exclude_layer=exclude_mask_layer)
    temp_dataset = density_result.dataset
    stats = density_result.stats
    output_driver.CreateCopy(output_path, temp_dataset)
    if do_print_stats:
        stats_dict = stats._asdict()
        stats_json = json.dumps(stats_dict, indent=2)

        print(stats_json)
