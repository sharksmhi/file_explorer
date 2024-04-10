import file_explorer
from file_explorer.tests.test_data import CNV_TEST_FILE
from file_explorer.tests.test_data import get_archive_path


def test_cruise_string_1():
    pack = file_explorer.get_package_for_file(CNV_TEST_FILE)
    file = pack.get_file(suffix='.cnv')
    assert file('cruise_string') == '77SE-2022-11'


def test_cruise_nr_1():
    pack = file_explorer.get_package_for_file(CNV_TEST_FILE)
    file = pack.get_file(suffix='.cnv')
    assert file('cruise') == '11'


def test_cruise_string_2():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'))
    pack = packs[key]
    file = pack.get_file(suffix='.cnv', tail='')
    assert file('cruise_string') == '2004'


def test_cruise_nr_2():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'))
    pack = packs[key]
    file = pack.get_file(suffix='.cnv', tail='')
    assert file('cruise') is False
