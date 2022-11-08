from pathlib import Path
import datetime

from file_explorer.file import InstrumentFile
from file_explorer.patterns import get_cruise_match_dict
from file_explorer import file_data


class TxtFile(InstrumentFile, file_data.DataFile):
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
        self._lat_dd = None
        self._lon_dd = None

        header = None
        with open(self.path) as fid:
            for line in fid:
                strip_line = line.strip()
                if not header and not line.startswith('//'):
                    header = [item.strip() for item in strip_line.split('\t')]
                    continue
                if header:
                    data_dict = dict(zip(header, [item.strip() for item in strip_line.split('\t')]))
                    self._lat_dd = float(data_dict['LATITUDE_DD'])
                    self._lon_dd = float(data_dict['LONGITUDE_DD'])
                    continue
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
        self._attributes['lat_dd'] = self._lat_dd
        self._attributes['lon_dd'] = self._lon_dd
        self._attributes['station'] = self._station
        self._attributes['cruise_info'] = self._cruise_info
        self._attributes['header_form'] = self._header_form
        self._attributes['metadata'] = self._metadata
        self._attributes['sensor_info'] = self._sensor_info
        self._attributes['qc'] = self._comment_qc
        self._attributes['parameters'] = self._parameters

    def _get_data_object(self):
        import pandas as pd
        from io import StringIO
        with open(self.path, encoding='cp1252') as fid:
            data = ''
            for line in fid:
                if line.startswith('//'):
                    continue
                data = data + line
        df = pd.read_csv(StringIO(data), sep='\t', encoding='cp1252')
        return file_data.Data(df)
