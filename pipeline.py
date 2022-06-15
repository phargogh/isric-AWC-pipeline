import argparse
import logging
import os

import numpy
import pygeoprocessing
import taskgraph
from osgeo import gdal

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('ISRIC-AWC')
URL_BASE = 'https://files.isric.org/soilgrids/former/2017-03-10/data'
ISRIC_2017_RASTERS = {
    '0cm': {
        'url': f'{URL_BASE}/WWP_M_sl1_250m_ll.tif',
        'md5': '0b6f02901c09f0a90dd11d889fce2ee3',
    },
    '5cm':   {
        'url': f'{URL_BASE}/WWP_M_sl2_250m_ll.tif',
        'md5': '6ade50398b3cbcadf0eba4c05a81251c',
    },
    '15cm':  {
        'url': f'{URL_BASE}/WWP_M_sl3_250m_ll.tif',
        'md5': 'e8efdbdd643e522d48cf73f7fe708180',
    },
    '30cm':  {
        'url': f'{URL_BASE}/WWP_M_sl4_250m_ll.tif',
        'md5': '92937d1547b09bfa7d3be40d72fe2792'
    },
    '60cm':  {
        'url': f'{URL_BASE}/WWP_M_sl5_250m_ll.tif',
        'md5': '4318e0098783d430ffc70f10b7505a75',
    },
    '100cm': {
        'url': f'{URL_BASE}/WWP_M_sl6_250m_ll.tif',
        'md5': 'e8d7ca1186906862e208549a205e1de8',
    },
    '200cm': {
        'url': f'{URL_BASE}/WWP_M_sl7_250m_ll.tif',
        'md5': '11a009837a8feebdd4af6569c029aa0d',
    },
}
NODATA_FLOAT32 = numpy.finfo(numpy.float32).min

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
    rasters = [
        soil_depth_0cm_path,
        soil_depth_5cm_path,
        soil_depth_15cm_path,
        soil_depth_30cm_path,
        soil_depth_60cm_path,
        soil_depth_100cm_path,
        soil_depth_200cm_path,
    ]
    expected_nodata = 255
    nodatas = [
        pygeoprocessing.get_raster_info(path)['nodata'][0] for path in rasters]
    assert nodatas == [expected_nodata]*len(nodatas)

    def _calculate(soil_depth_0cm, soil_depth_5cm, soil_depth_15cm,
                   soil_depth_30cm, soil_depth_60cm, soil_depth_100cm,
                   soil_depth_200cm):
        awc = numpy.full(soil_depth_0cm.shape, NODATA_FLOAT32,
                         dtype=numpy.float32)
        valid_mask = numpy.ones(soil_depth_0cm.shape, dtype=bool)
        for array in [soil_depth_0cm, soil_depth_5cm, soil_depth_15cm,
                      soil_depth_30cm, soil_depth_60cm, soil_depth_100cm,
                      soil_depth_200cm]:
            valid_mask &= (array != 255)

        awc[valid_mask] = ((1/200) * 1/2 * (
            ((5 - 0) * (soil_depth_0cm[valid_mask] + soil_depth_5cm[valid_mask])) +
            ((15 - 5) * (soil_depth_5cm[valid_mask] + soil_depth_15cm[valid_mask])) +
            ((30 - 15) * (soil_depth_15cm[valid_mask] + soil_depth_30cm[valid_mask])) +
            ((60 - 30) * (soil_depth_30cm[valid_mask] + soil_depth_60cm[valid_mask])) +
            ((100 - 60) * (soil_depth_60cm[valid_mask] + soil_depth_100cm[valid_mask])) +
            ((200 - 100) * (soil_depth_100cm[valid_mask] + soil_depth_200cm[valid_mask])))
        ) / 100
        return awc


    # TODO: make this a COG
    # TODO: be sure to compress the output raster
    # TODO: build overviews as well before upload.
    # TODO: build in some warnings if the values are outside of the expected
    # range of 0-100 (or 0-1 if we've already divided by 100).
    driver_opts = ('GTIFF', (
    'TILED=YES', 'BIGTIFF=YES', 'COMPRESS=LZW',
    'BLOCKXSIZE=256', 'BLOCKYSIZE=256', 'PREDICTOR=3', 'NUM_THREADS=4'))
    pygeoprocessing.geoprocessing.raster_calculator(
        [(path, 1) for path in rasters], _calculate, target_awc_path,
        gdal.GDT_Float32, float(NODATA_FLOAT32))


def main():
    # do an argparse interface.
    # create a graph of tasks
    # For each of the soils rasters:
    #   If the file isn't available locally (and checksum fails), download the file (retry if needed)
    #   Verify the checksum of the file for integrity
    # When the files are all downloaded, check alignment of layers and run
    # raster_calculator.
    soil_rasters = [os.path.basename(val['url']) for val in
                    ISRIC_2017_RASTERS.values()]
    calculate_awc(*soil_rasters, 'awc_frac.tif')


if __name__ == '__main__':
    main()
