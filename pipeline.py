import logging
import argparse

import pygeoprocessing
import numpy
import taskgraph

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('ISRIC-AWC')
URL_BASE = 'https://files.isric.org/soilgrids/former/2017-03-10/data'
ISRIC_2017_RASTERS = {
    '0cm':   f'{URL_BASE}/WWP_M_sl1_250m_ll.tif',
    '5cm':   f'{URL_BASE}/WWP_M_sl2_250m_ll.tif',
    '15cm':  f'{URL_BASE}/WWP_M_sl3_250m_ll.tif',
    '30cm':  f'{URL_BASE}/WWP_M_sl4_250m_ll.tif',
    '60cm':  f'{URL_BASE}/WWP_M_sl5_250m_ll.tif',
    '100cm': f'{URL_BASE}/WWP_M_sl6_250m_ll.tif',
    '200cm': f'{URL_BASE}/WWP_M_sl7_250m_ll.tif',
}


def fetch_raster(source_raster_path, dest_raster_path, checksum):
    pass


def calculate_awc(
        soil_depth_0cm_path,
        soil_depth_5cm_path,
        soil_depth_15cm_path,
        soil_depth_30cm_path,
        soil_depth_60cm_path,
        soil_depth_100cm_path,
        soil_depth_200cm_path,
        target_awc_path):
    # determine nodata values for each layer.

    def _calculate():
        pass

    # TODO: make this a COG
    # TODO: be sure to compress the output raster
    # TODO: build overviews as well before upload.
    # TODO: build in some warnings if the values are outside of the expected
    # range of 0-100 (or 0-1 if we've already divided by 100).
    pygeoprocessing.raster_calculator()


def main():
    # do an argparse interface.
    # create a graph of tasks
    # For each of the soils rasters:
    #   If the file isn't available locally (and checksum fails), download the file (retry if needed)
    #   Verify the checksum of the file for integrity
    # When the files are all downloaded, check alignment of layers and run
    # raster_calculator.
    pass


if __name__ == '__main__':
    main()
