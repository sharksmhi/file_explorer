import datetime

from file_explorer.file import InstrumentFile
from file_explorer.patterns import get_cruise_match_dict


class DatFile(InstrumentFile):
    suffix = '.dat'
    date_format = '%b %d %Y %H:%M:%S'

    def _save_info_from_file(self):
        self._cruise_info = {}
        self._header_form = {'info': []}
        with open(self.path) as fid:
            for line in fid:
                strip_line = line.strip()
                if line.startswith('* System UpLoad Time'):
                    self._datetime = datetime.datetime.strptime(line.split('=')[1].strip(), self.date_format)
                elif line.startswith('** Latitude'):
                    self._lat = line.split(':', 1)[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Longitude'):
                    self._lon = line.split(':', 1)[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Station'):
                    self._station = line.split(':')[-1].strip()
                elif line.startswith('** Ship'):
                    self._ship = line.split(':')[-1].strip()
                elif line.startswith('** Cruise'):
                    self._cruise_info = get_cruise_match_dict(line.split(':')[-1].strip())
                if line.startswith('**'):
                    if line.count(':') == 1:
                        key, value = [part.strip() for part in line.strip().strip('*').split(':', 1)]
                        self._header_form[key] = value
                    else:
                        self._header_form['info'].append(strip_line)

    def _save_attributes(self):

        self._attributes.update(dict((key.lower(), value) for key, value in self._header_form.items()))
        self._attributes.update(dict((key.lower(), value) for key, value in self._cruise_info.items()))
        self._attributes.update(self._cruise_info)
        self._attributes['lat'] = self._lat
        self._attributes['lon'] = self._lon
        self._attributes['station'] = self._station
        self._attributes['ship'] = self._ship
        self._attributes['cruise_info'] = self._cruise_info
        self._attributes['header_form'] = self._header_form
