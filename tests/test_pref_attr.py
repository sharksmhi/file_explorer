import file_explorer
from file_explorer.tests.test_data import LOCAL_TEST_DIR


def test_pref_attribute():
    packs = file_explorer.get_packages_in_directory(LOCAL_TEST_DIR)
    pack = packs['SBE09_1387_20220918_1305_77SE_16_0847']
    assert pack('station') == 'BY4 CHRISTIANS'
    assert pack('station', pref_suffix='.hdr') == 'BY4 CHRISTIANSÖ'