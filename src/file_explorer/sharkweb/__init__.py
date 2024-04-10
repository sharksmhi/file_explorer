from .physical_chemical import get_metadata_from_sharkweb_btl_data
from . import api
from file_explorer import utils
import requests


def download_data_from_sharkweb(from_year: int, to_year: int = None):
    to_year = to_year or from_year
    temp_dir = utils.get_temp_directory('sharkweb_data')
    print(f'{temp_dir}')
    try:
        file_paths = api.SHARKwebAPI(result_directory=utils.get_temp_directory('sharkweb_data')).save_files(datatypes=['Physical and Chemical'],
                                                                                year_interval=[from_year, to_year])
    except requests.exceptions.ConnectionError:
        return None
    return file_paths
