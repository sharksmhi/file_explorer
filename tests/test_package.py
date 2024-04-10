import datetime
import file_explorer
from file_explorer.tests.test_data import TEST_DATA_DIR
from file_explorer.tests.test_data import CNV_TEST_FILE
from file_explorer.tests.test_data import LOCAL_TEST_DIR


def test_package_nr_packs():
    packs1 = file_explorer.get_packages_in_directory(TEST_DATA_DIR)
    packs2 = file_explorer.get_packages_in_directory(TEST_DATA_DIR, with_id_as_key=True)
    packs3 = file_explorer.get_packages_in_directory(TEST_DATA_DIR, as_list=True)

    assert len(packs1) == 5
    assert len(packs2) == 4
    assert len(packs3) == 5


def test_package_nr_packs_exclude_directory():
    packs = file_explorer.get_packages_in_directory(TEST_DATA_DIR, as_list=True, exclude_directory='arkiv_2004')
    assert len(packs) == 4


def test_package_id_as_key():
    packs = file_explorer.get_packages_in_directory(TEST_DATA_DIR, with_id_as_key=True)
    assert 'SBE09_1387_77SE_0511' in packs
    assert 'SBE09_1387_20220613_1800_77SE_11_0511' not in packs


def test_package_no_datetime_from_file_name():
    pack_false = file_explorer.get_package_for_file(CNV_TEST_FILE, no_datetime_from_file_name=False)
    pack_true = file_explorer.get_package_for_file(CNV_TEST_FILE, no_datetime_from_file_name=True)
    pack_default = file_explorer.get_package_for_file(CNV_TEST_FILE)

    d_false = datetime.datetime(2022, 6, 13, 18, 0)
    d_true = datetime.datetime(2022, 6, 13, 18, 2, 4)

    assert pack_false.datetime == d_false
    assert pack_true.datetime == d_true
    assert pack_default.datetime == d_false


def test_suffix_in_package():
    packs = file_explorer.get_packages_in_directory(LOCAL_TEST_DIR)
    pack = packs['SBE09_1387_20220823_1041_77SE_14_0600']
    nr_suffix = len(set([file.suffix for file in pack.files]))
    assert nr_suffix == 12



