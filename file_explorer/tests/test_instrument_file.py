import datetime
import pathlib

from file_explorer.file import InstrumentFile
from file_explorer.tests.test_data import HEX_TEST_FILE

#  For testing a ABC: https://clamytoe.github.io/articles/2020/Mar/12/testing-abcs-with-abstract-methods-with-pytest/



def test_instrument_file_encoding_default():
    InstrumentFile.__abstractmethods__ = set()

    class Dummy(InstrumentFile):
        suffix = '.hex'

    dummy = Dummy(HEX_TEST_FILE)

    assert dummy.encoding == 'cp1252'


def test_instrument_file_encoding_given_to_current_file():
    InstrumentFile.__abstractmethods__ = set()

    class Dummy(InstrumentFile):
        suffix = '.hex'

    dummy = Dummy(HEX_TEST_FILE, hex_encoding='utf8')

    assert dummy.encoding == 'utf8'


def test_instrument_file_encoding_given_to_other_file():
    InstrumentFile.__abstractmethods__ = set()

    class Dummy(InstrumentFile):
        suffix = '.hex'

    dummy = Dummy(HEX_TEST_FILE, btl_encoding='utf8')

    assert dummy.encoding == 'cp1252'


def test_instrument_file_attributes_call():
    InstrumentFile.__abstractmethods__ = set()

    class Dummy(InstrumentFile):
        suffix = '.hex'

    dummy = Dummy(HEX_TEST_FILE)

    assert dummy('suffix') == '.hex'
    assert dummy('path') == str(HEX_TEST_FILE)
    assert dummy('name') == HEX_TEST_FILE.name

    assert dummy('datetime') == datetime.datetime(2022, 6, 13, 18, 0)
    assert dummy('date') == '2022-06-13'
    assert dummy('time') == '18:00'
