import file_explorer
from file_explorer.tests.test_data import get_archive_path

KEY1_NR_FILES = 6


def test_nr_files_in_package_exclude_nothing():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'))
    pack = packs[key]
    assert pack.nr_of_files == KEY1_NR_FILES


def test_nr_files_in_package_exclude_suffix():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'), exclude_suffix='.zip')
    pack = packs[key]
    assert pack.nr_of_files == KEY1_NR_FILES - 1


def test_nr_files_in_package_exclude_string():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'), exclude_string='_ver_')
    pack = packs[key]
    assert pack.nr_of_files == KEY1_NR_FILES - 1


def test_nr_files_in_package_exclude_suffix_and_string():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'), exclude_suffix='.zip', exclude_string='_ver_')
    pack = packs[key]
    assert pack.nr_of_files == KEY1_NR_FILES - 2

