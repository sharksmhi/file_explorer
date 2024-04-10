import pathlib

TEST_DATA_DIR = pathlib.Path(__file__).parent.absolute()


HEX_TEST_FILE = pathlib.Path(TEST_DATA_DIR, 'SBE09_1387_20220613_1800_77SE_11_0511.hex')
HDR_TEST_FILE = pathlib.Path(TEST_DATA_DIR, 'SBE09_1387_20220613_1800_77SE_11_0511.hdr')
CNV_TEST_FILE = pathlib.Path(TEST_DATA_DIR, 'SBE09_1387_20220613_1800_77SE_11_0511.cnv')
CNV_TEST_FILE_2 = pathlib.Path(TEST_DATA_DIR, 'SBE09_1387_20220613_1802_77SE_11_0511.cnv')
LOCAL_TEST_DIR = pathlib.Path(TEST_DATA_DIR, 'local')


def get_archive_path(year):
    path = pathlib.Path(TEST_DATA_DIR, f'arkiv_{year}')
    if not path.exists():
        raise NotADirectoryError(path)
    return path
