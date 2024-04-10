import datetime
from pathlib import Path

from file_explorer.file import InstrumentFile
from file_explorer.patterns import get_cruise_match_dict
from file_explorer.seabird import utils


class HdrFile(InstrumentFile):
    suffix = '.hdr'
    date_format = '%b %d %Y %H:%M:%S'
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
                strip_line = line.strip()
                if line.startswith('* System UTC'):
                    self._datetime = datetime.datetime.strptime(line.split('=')[1].strip(), self.date_format)
                elif line.startswith('* NMEA Latitude'):
                    self._lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('* NMEA Longitude'):
                    self._lon = line.split('=')[1].strip()[:-1].replace(' ', '')
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

