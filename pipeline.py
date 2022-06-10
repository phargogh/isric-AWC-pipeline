import logging
import argparse

import pygeoprocessing
import numpy
import taskgraph

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('ISRIC-AWC')


def fetch_raster(source_raster_path, dest_raster_path, checksum):
    pass

def calculate_awc(
        depth_0cm_path,
        depth_5cm_path,
        depth_15cm_path,
        depth_30cm_path,
        depth_60cm_path,
        depth_100cm_path,
        depth_200cm_path,
        target_awc_path):
    # determine nodata values for each layer.

    def _calculate():
        pass

    # TODO: make this a COG
    # TODO: be sure to compress the output raster
    # TODO: build overviews as well before upload.
    pygeoprocessing.raster_calculator()


def main():
    # do an argparse interface.
    # create a graph of tasks
    # For each of the soils rasters:
    #   Download the file (retry if needed)
    #   Verify the checksum of the file for integrity
    # When the files are all downloaded, check alignment of layers and run
    # raster_calculator.
    pass


if __name__ == '__main__':
    main()
