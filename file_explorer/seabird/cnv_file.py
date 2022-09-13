import datetime

import pathlib
from file_explorer import mapping
from file_explorer.file import InstrumentFile
from file_explorer.patterns import get_cruise_match_dict
from file_explorer.seabird import xmlcon_parser
from file_explorer import file_data

from file_explorer.seabird import utils

import logging

logger = logging.getLogger(__name__)


class CnvFile(InstrumentFile, file_data.DataFile):
    suffix = '.cnv'
    header_date_format = '%b %d %Y %H:%M:%S'
    header = None
    _header_datetime = None
    _header_lat = None
    _header_lon = None
    _header_station = None
    _header_form = None
    _header_names = None
    _header_cruise_info = None
    _xml_tree = None
    _parameters = {}
    _sensor_info = None
    _nr_data_lines = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_save_name(self):
        if self('prefix') == 'd':
            return f'{self.key}{self.suffix}'
        return self.get_proper_name()

    def validate(self, case_sensitive=True):
        data = {}
        file_name_datetime = self._get_datetime_from_path(force=True)
        if file_name_datetime != self._header_datetime:
            data['datetime mismatch in cnv'] = f'{file_name_datetime} in file name. ' \
                                               f'{self._header_datetime} in file header'
        return data

    def _get_datetime(self):
        return self._header_datetime or self._get_datetime_from_path()

    def _save_attributes(self):
        self._attributes.update(dict((key.lower(), value) for key, value in self._header_form.items()))
        self._attributes.update(dict((key.lower(), value) for key, value in self._header_cruise_info.items()))
        self._attributes['lat'] = self._header_lat
        self._attributes['lon'] = self._header_lon
        self._attributes['station'] = self._header_station
        self._attributes['sensor_info'] = self._sensor_info
        self._attributes['cruise_info'] = self._header_cruise_info
        self._attributes['header_form'] = self._header_form
        self._attributes['nr_data_lines'] = self._nr_data_lines
        self._attributes['header_names'] = self._header_names

    def _save_info_from_file(self):
        self._header_form = {'info': []}
        self._header_names = []
        self._nr_data_lines = 0
        self._parameters = {}
        self._header_cruise_info = {}
        self._psa_info = {}
        self._psa_header_keys = ['datcvn', 'filter', 'celltm', 'loopedit', 'derive', 'split']

        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>\n']
        is_xml = False

        with open(self.path) as fid:
            for line in fid:

                # General header info
                if line.startswith('* System UTC'):
                    self._header_datetime = datetime.datetime.strptime(line.split('=')[1].strip(),
                                                                       self.header_date_format)
                elif line.startswith('* NMEA Latitude') and '=' in line:
                    self._header_lat = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('* NMEA Longitude') and '=' in line:
                    self._header_lon = line.split('=')[1].strip()[:-1].replace(' ', '')
                elif line.startswith('** Station'):
                    self._header_station = line.split(':')[-1].strip()
                elif line.startswith('** Cruise'):
                    self._header_cruise_info = get_cruise_match_dict(line.split(':')[-1].strip())

                # Header form
                elif line.startswith('**'):
                    attrs = utils.get_dict_from_header_form_line(line)
                    self._header_form.update(attrs)

                # psa info
                self._add_psa_info(line)

                # XML
                if line.startswith('# <Sensors count'):
                    is_xml = True
                if is_xml:
                    xml_lines.append(line[2:])
                if line.startswith('# </Sensors>'):
                    is_xml = False
                    self._xml_tree = xmlcon_parser.get_parser_from_string(''.join(xml_lines))
                    logger.debug(self.path)
                    self._sensor_info = xmlcon_parser.get_sensor_info(self._xml_tree)

    def _add_psa_info(self, line):
        if not line.startswith('#'):
            return
        line = line.strip('# ')
        split_line = [item.strip() for item in line.split('=', 1)]
        split_line[0] = split_line[0].lower()
        if not split_line[0].split('_')[0] in self._psa_header_keys:
            return
        if 'date' in split_line[0]:
            return
        if 'time' in split_line[0]:
            return
        if split_line[0].endswith('_in'):
            return
        self._psa_info[split_line[0]] = split_line[1]

    @property
    def psa_info(self):
        return self._psa_info

    def set_nmea_pos(self, directory=None, subdir=None, overwrite=False):
        if not self.edit_mode:
            raise Exception(f'{__class__} object is not in edit_mode: {self.path}')
        path = self.path
        if directory:
            path = pathlib.Path(directory, path.name)
        if subdir:
            path = pathlib.Path(path.parent, subdir, path.name)
        if path.exists() and not overwrite:
            raise FileExistsError(path)
        lat_str = '* NMEA Latitude:'
        lon_str = '* NMEA Longitude:'
        pos = None
        lines = []
        lat_index = None
        lon_index = None
        with open(self.path) as fid:
            for i, line in enumerate(fid):
                lines.append(line)
                if not lat_index and line.startswith(lat_str):
                    lat_index = i
                if not lon_index and line.startswith(lon_str):
                    lon_index = i
                if not pos:
                    pos = utils.get_nmea_pos_from_header_form_line(line)
        if not pos:
            return False
        lines[lat_index] = f'{lat_str} {pos[0]}\n'
        lines[lon_index] = f'{lon_str} {pos[1]}\n'

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding=self.encoding) as fid:
            fid.write(''.join(lines))
        return path

    def _get_data_object(self):
        import pandas as pd
        from io import StringIO
        metadata = True
        header = []
        with open(self.path, encoding=self.encoding) as fid:
            data = []
            for line in fid:
                if not line.strip():
                    continue
                if line.strip() == '*END*':
                    metadata = False
                    data.append('\t'.join(header))
                elif line.startswith('# name'):
                    par = line.split(':', 1)[-1].strip()
                    header.append(par)
                elif metadata:
                    continue
                else:
                    data.append('\t'.join(line.split()))
        df = pd.read_csv(StringIO('\n'.join(data)), sep='\t', encoding='cp1252')
        return file_data.Data(df)
