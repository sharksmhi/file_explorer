from pathlib import Path
import datetime

from file_explorer.file import InstrumentFile
from file_explorer.patterns import get_cruise_match_dict


class TxtFile(InstrumentFile):
    suffix = '.txt'
    date_format = '%b %d %Y %H:%M:%S'
    _datetime = None
    _station = None
    _metadata = None
    _header_form = None
    _lat = None
    _lon = None

    def _get_datetime(self):
        return self._datetime

    def _save_info_from_file(self):
        self._metadata = {}
        self._sensor_info = []
        self._instrument_metadata = []
        sensor_info_header = None
        self._header_form = {'info': []}
        self._cruise_info = {}
        self._comment_qc = []
        self._parameters = None

        with open(self.path) as fid:
            for line in fid:
                strip_line = line.strip()
                if strip_line.startswith('//METADATA;'):
                    m, key, value = strip_line.split(';', 2)
                    self._metadata[key] = value
                elif strip_line.startswith('//SENSORINFO;'):
                    parts = strip_line.split(';')
                    if sensor_info_header:
                        self._sensor_info.append(dict(zip(sensor_info_header, parts[1:])))
                    else:
                        sensor_info_header = parts[1:]
                elif strip_line.startswith('//INSTRUMENT_METADATA;'):
                    data = strip_line.split(';', 1)[1]
                    self._instrument_metadata.append(data)
                    if data.startswith('* System UTC'):
                        self._datetime = datetime.datetime.strptime(data.split('=')[1].strip(), self.date_format)
                    elif data.startswith('* NMEA Latitude'):
                        self._lat = data.split('=')[1].strip()[:-1].replace(' ', '')
                    elif data.startswith('* NMEA Longitude'):
                        self._lon = data.split('=')[1].strip()[:-1].replace(' ', '')
                    elif data.startswith('** Station'):
                        self._station = data.split(':')[-1].strip()
                    elif data.startswith('** Cruise'):
                        self._cruise_info = get_cruise_match_dict(data.split(':')[-1].strip())
                    if data.startswith('**'):
                        if data.count(':') == 1:
                            key, value = [part.strip() for part in data.strip().strip('*').split(':')]
                            self._header_form[key] = value
                        else:
                            self._header_form['info'].append(strip_line)
                elif strip_line.startswith('//COMNT_QC;'):
                    self._comment_qc.append(strip_line.split(';', 1)[1])
                elif not strip_line.startswith('//') and not self._parameters:
                    self._parameters = [item for item in strip_line.split() if item[:2] not in ['Q_', 'Q0']]

    def _save_attributes(self):
        self._attributes.update(dict((key.lower(), value) for key, value in self._header_form.items()))
        self._attributes.update(dict((key.lower(), value) for key, value in self._cruise_info.items()))
        self._attributes.update(dict((key.lower(), value) for key, value in self._metadata.items()))
        self._attributes['lat'] = self._lat
        self._attributes['lon'] = self._lon
        self._attributes['station'] = self._station
        self._attributes['cruise_info'] = self._cruise_info
        self._attributes['header_form'] = self._header_form
        self._attributes['metadata'] = self._metadata
        self._attributes['sensor_info'] = self._sensor_info
        self._attributes['qc'] = self._comment_qc
        self._attributes['parameters'] = self._parameters

    @property
    def data(self):
        import pandas as pd
        from io import StringIO
        with open(self.path, encoding='cp1252') as fid:
            data = ''
            for line in fid:
                if line.startswith('//'):
                    continue
                data = data + line
        df = pd.read_csv(StringIO(data), sep='\t', encoding='cp1252')
        return df
