import datetime
import re

from file_explorer.file import InstrumentFile
from file_explorer.patterns import get_cruise_match_dict
from file_explorer.seabird import utils


class HexFile(InstrumentFile):
    suffix = '.hex'
    date_format = '%d %b %Y %H:%M:%S'
    _datetime = None
    _station = None
    _cruise_info = {}
    _header_form = {}

    def _get_datetime(self):
        return self._datetime

    def _save_info_from_file(self):
        self._cruise_info = {}
        self._header_form = {'info': []}
        with open(self.path) as fid:
            for line in fid:
                if line.startswith('* cast'):
                    reg = re.search(r'\d{1,2} \D{3} \d{4} \d{2}:\d{2}:\d{2}', line)
                    if not reg:
                        continue
                    self._datetime = datetime.datetime.strptime(reg.group(), self.date_format)
                elif line.startswith('** Latitude'):
                    reg = re.search(r'\d{2} \d{2}.\d{1,2}', line)
                    if not reg:
                        continue
                    self._lat = reg.group().replace(' ', '')
                elif line.startswith('** Longitude'):
                    reg = re.search(r'\d{2} \d{2}.\d{1,2}', line)
                    if not reg:
                        continue
                    self._lon = reg.group().replace(' ', '')
                elif line.startswith('** Station'):
                    self._station = line.split(':')[-1].strip()
                elif line.startswith('** Cruise'):
                    self._cruise_info = get_cruise_match_dict(line.split(':')[-1].strip())
                elif line.startswith('**'):
                    # Header form
                    attrs = utils.get_dict_from_header_form_line(line)
                    self._header_form.update(attrs)

    def _save_attributes(self):
        self._attributes.update(dict((key.lower(), value) for key, value in self._header_form.items()))
        self._attributes.update(dict((key.lower(), value) for key, value in self._cruise_info.items()))
        self._attributes['lat'] = self._lat
        self._attributes['lon'] = self._lon
        self._attributes['station'] = self._station
        self._attributes['cruise_info'] = self._cruise_info
        self._attributes['header_form'] = self._header_form
