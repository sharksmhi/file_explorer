import pytest

from file_explorer.seabird import HdrFile
from file_explorer.tests.test_data import HDR_TEST_FILE


@pytest.fixture
def hdr_obj():
    return HdrFile(HDR_TEST_FILE)


def test_hdr_file_date_format(hdr_obj):
    assert hdr_obj.date_format == '%b %d %Y %H:%M:%S'


def test_hdr_file_pos(hdr_obj):
    assert hdr_obj('lat') == '5856.19'
    assert hdr_obj('lon') == '01909.31'


def test_hdr_file_metadata(hdr_obj):
    assert hdr_obj('primarypump') == '6060'
    assert hdr_obj('eventid') == ''
    assert hdr_obj('winsp') == '8'
    assert hdr_obj('lims job') == '20227710-0511'



