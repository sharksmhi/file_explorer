import file_explorer
from file_explorer.tests.test_data import get_archive_path


def test_same_file_content():
    key = 'SBE09_0745_20040628_1348_77_14_0420'
    packs = file_explorer.get_packages_in_directory(get_archive_path('2004'))
    pack = packs[key]
    cnv_files = pack.get_files(suffix='.cnv')
    assert cnv_files[0] == cnv_files[1]
