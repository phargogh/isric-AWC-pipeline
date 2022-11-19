import argparse
import hashlib
import http.client
import logging
import os
import shutil

import appdirs
import numpy
import pygeoprocessing
import requests
import urllib3.exceptions
from osgeo import gdal

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('ISRIC-AWC')
URL_BASE = 'https://files.isric.org/soilgrids/former/2017-03-10/data'
ISRIC_2017_WWP_RASTERS = {
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
ISRIC_2017_AWCH1_RASTERS = {
    '0cm': {
        'url': f'{URL_BASE}/AWCh1_M_sl1_250m_ll.tif',
        'md5': '1524105262f5c4d520c9fe78fea5d41f',
    },
    '5cm':   {
        'url': f'{URL_BASE}/AWCh1_M_sl2_250m_ll.tif',
        'md5': '28ff1f7b89d71c1be90ab24a808cc2a3',
    },
    '15cm':  {
        'url': f'{URL_BASE}/AWCh1_M_sl3_250m_ll.tif',
        'md5': '7fdeb76f5343728c554f98e3f276e31d',
    },
    '30cm':  {
        'url': f'{URL_BASE}/AWCh1_M_sl4_250m_ll.tif',
        'md5': '132e3d5e277dc4991e66ab3ef3914237'
    },
    '60cm':  {
        'url': f'{URL_BASE}/AWCh1_M_sl5_250m_ll.tif',
        'md5': '9d6388d9a920734440026235b9f8eddf',
    },
    '100cm': {
        'url': f'{URL_BASE}/AWCh1_M_sl6_250m_ll.tif',
        'md5': '07b2f481f5b84dedadde0bb0e4d69d7d',
    },
    '200cm': {
        'url': f'{URL_BASE}/AWCh1_M_sl7_250m_ll.tif',
        'md5': '65eda75f1624d8ba6725f3d1820d5ac5',
    },
}
NODATA_FLOAT32 = numpy.finfo(numpy.float32).min


def _digest_file(filepath, alg):
    m = hashlib.new(alg)
    with open(filepath, 'rb') as binary_file:
        while True:
            chunk = binary_file.read(2048)
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest()


def fetch_raster(source_raster_url, dest_raster_path, checksum_alg, checksum):
    r = requests.head(source_raster_url)
    target_file_size_bytes = int(r.headers.get('content-length', 0))
    LOGGER.info(f"Downloading {source_raster_url}, "
                f"{target_file_size_bytes} bytes")
    resume_header = None

    def _filesize(path):
        try:
            return os.path.getsize(path)
        except OSError:
            # If file does not yet exist
            return 0

    bytes_written = 0
    n_retries = 0
    while _filesize(dest_raster_path) < target_file_size_bytes:
        try:
            LOGGER.info(
                f"Downloading {dest_raster_path}, {bytes_written}b so far")
            if n_retries:
                LOGGER.info(f"{n_retries} retries so far")
            with requests.get(source_raster_url,
                              stream=True, headers=resume_header) as r:
                with open(dest_raster_path, 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
        except (http.client.IncompleteRead,
                urllib3.exceptions.ProtocolError) as error:
            n_retries += 1
            bytes_written = _filesize(dest_raster_path)
            LOGGER.exception(error)
            LOGGER.info(f'Download failed, restarting from {bytes_written}')
            resume_header = {'Range': f'bytes={bytes_written}'}

    LOGGER.info(f"Downloaded {source_raster_url}")

    if _digest_file(dest_raster_path, checksum_alg) != checksum:
        raise RuntimeError(f"Checksums do not match on {dest_raster_path}")


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

        awc[valid_mask] = ((1/200) * (1/2) * (
            ((5 - 0) * (soil_depth_0cm[valid_mask] + soil_depth_5cm[valid_mask])) +
            ((15 - 5) * (soil_depth_5cm[valid_mask] + soil_depth_15cm[valid_mask])) +
            ((30 - 15) * (soil_depth_15cm[valid_mask] + soil_depth_30cm[valid_mask])) +
            ((60 - 30) * (soil_depth_30cm[valid_mask] + soil_depth_60cm[valid_mask])) +
            ((100 - 60) * (soil_depth_60cm[valid_mask] + soil_depth_100cm[valid_mask])) +
            ((200 - 100) * (soil_depth_100cm[valid_mask] + soil_depth_200cm[valid_mask])))
        ) / 100
        return awc


    # TODO: build overviews as well before upload.
    # TODO: build in some warnings if the values are outside of the expected
    # range of 0-100 (or 0-1 if we've already divided by 100).
    driver_opts = ('GTIFF', (
    'TILED=YES', 'BIGTIFF=YES', 'COMPRESS=LZW',
    'BLOCKXSIZE=256', 'BLOCKYSIZE=256', 'PREDICTOR=1', 'NUM_THREADS=4'))
    raster_paths = [(path, 1) for path in rasters]
    pygeoprocessing.geoprocessing.raster_calculator(
        raster_paths, _calculate, target_awc_path,
        gdal.GDT_Float32, float(NODATA_FLOAT32))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--cache-dir', default=appdirs.user_cache_dir('isric-awc', 'natcap'))
    parser.add_argument('target_awc')

    parsed_args = parser.parse_args()

    cache_dir = os.path.abspath(parsed_args.cache_dir)
    if not os.path.exists(cache_dir):
        os.mkdirs(cache_dir)

    LOGGER.info(f"Looking for existing AWC rasters in {cache_dir}")

    local_soil_rasters = []
    for soil_raster_dict in ISRIC_2017_AWCH1_RASTERS.values():
        local_file = os.path.join(
            cache_dir, os.path.basename(soil_raster_dict['url']))
        if not os.path.exists(local_file):
            LOGGER.info(f"File not found: {local_file}")
            fetch_raster(soil_raster_dict['url'], local_file, 'md5',
                         soil_raster_dict['md5'])
        else:
            LOGGER.info(f"Verifying checksum on {local_file}")
            if not _digest_file(local_file, 'md5') == soil_raster_dict['md5']:
                raise AssertionError(
                    "MD5sum for {local_file} did not match what's expected. "
                    "Try deleting the file and re-running the program to "
                    "re-download the file.")
        local_soil_rasters.append(local_file)

    LOGGER.info(f"Calculating AWC to {parsed_args.target_awc}")
    calculate_awc(*local_soil_rasters, parsed_args.target_awc)

    LOGGER.info(f"AWC complete; written to {parsed_args.target_awc}")


if __name__ == '__main__':
    main()
