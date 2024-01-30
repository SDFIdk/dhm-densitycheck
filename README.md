# dhm-densitycheck
Tool to check point density of point cloud deliverables.

## Installation

An appropriate environment (here named `densitycheck`) can be created with:

```
conda env create -n densitycheck -f environment.yml
```

The tool supports editable installation using `pip`. To install it this way,
use the following command in the root directory:

```
pip install -e .
```

You may want to test your installation by calling `pytest` in the root
directory.

## Usage

The tool is intended to be used on a single pointcloud tile, producing a raster
of point densities with density (points per georeferenced area unit) reported
per raster cell. The spatial extent is automatically computed. The command to
use is:

```
point_density [-h] [--cell-size CELL_SIZE] [--returns {ALL,FIRST,LAST}] input_las output_raster
```

| Parameter | Description |
| --------- | ----------- |
| `input_las` | Path to `laspy`-readable pointcloud file (LAS, LAZ, COPC) |
| `output_raster` | Path to desired output raster file. Will be written as COG (Cloud-Optimized GeoTIFF) |
| `--cell-size CELL_SIZE` | Size of cells in output raster in georeferenced units (commonly meters) |
| `--returns {ALL,FIRST,LAST}` | Consider only points with these return numbers |
| `-h` | Print help and exit |

## Example

This will create a COG raster with 10-meter cells, containing number of points
per square meter in each cell:

```
point_density 1km_1234_567.laz 1km_1234_567_density.tif --cell-size 10.0
```
