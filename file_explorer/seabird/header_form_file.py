import pathlib
from pathlib import Path
import logging
import re
from abc import ABC, abstractmethod

from typing import List

from file_explorer.seabird.hdr_file import HdrFile
from file_explorer.seabird.hex_file import HexFile

from file_explorer.seabird import utils
from file_explorer.file_explorer_logger import fe_logger


logger = logging.getLogger(__name__)

HEADER_FORM_PREFIX = '**'

HEADER_FORM_KEYS = {
                '** Station:': '** Sta',
                '** Operator:': '** Ope',
                '** Ship:': '** Shi',
                '** Cruise:': '** Cru',
                '** Latitude [GG MM.mm N]:': '** Lat',
                '** Longitude [GGG MM.mm E]:': '** Lon',
                '** Pumps: #': '** Pum',
                '** EventIDs: #': '** Eve',
                '** Additional Sampling:': '** Add',
                '** Metadata admin: #': '** Metadata adm',
                '** Metadata conditions: #': '** Metadata con',
                '** LIMS Job:': '** LIM',
                    }


HEADER_FIELDS = (
    'Station',
    'Operator',
    'Ship',
    # 'Average sound velocity',
    # 'True-depth calculation',
    'Cruise',
    'Latitude [GG MM.mm N]',
    'Longitude [GGG MM.mm E]',
    'Pumps',
    'EventIDs',
    'Additional Sampling',
    'Metadata admin',
    'Metadata conditions',
    'LIMS Job',
)


PUMPS_LIST = (
    'PrimaryPump',
    'SecondaryPump'
)


EVENT_IDS_LIST = (
    'EventID',
    'ParentEventID'
)


METADATA_ADMIN_LIST = (
    'MPROG',
    'PROJ',
    'ORDERER',
    'SLABO',
    'ALABO',
    'REFSK'
)


METADATA_CONDITIONS_LIST = (
    # 'WADEP_BOT',
    'WADEP',
    'WINDIR',
    'WINSP',
    'AIRTEMP',
    'AIRPRES',
    'WEATH',
    'CLOUD',
    'WAVES',
    'ICEOB',
    'COMNT_VISIT'
)

NMEA_FIELDS = [
    '* NMEA Latitude = ',
    '* NMEA Longitude = ',
    '* NMEA UTC (Time) = '
]


def strip_meta_key(meta):
    return meta.strip('* :').lower().split()[0]


META_MAPPING = {strip_meta_key(key): key for key in HEADER_FIELDS + METADATA_ADMIN_LIST + METADATA_CONDITIONS_LIST + PUMPS_LIST + EVENT_IDS_LIST}


def get_mapped_meta(key):
    return META_MAPPING[strip_meta_key(key)]


class InfoLine(ABC):

    def __init__(self, line: str) -> None:
        if not line.startswith('* '):
            raise Exception(f'Invalid {self.__class__.__name__}: {line}')
        self._line = line.strip()
        self._check_if_valid()
        self._save_info()

    def __str__(self):
        return self.get_line()

    @property
    def key_string(self):
        return self._line.strip('* ').split('=', 1)[0].strip()

    @abstractmethod
    def _check_if_valid(self):
        ...

    @abstractmethod
    def _save_info(self):
        ...

    @abstractmethod
    def get_line(self):
        ...

    @abstractmethod
    def set_value(self, *args, **kwargs):
        ...

    @abstractmethod
    def get_value(self, *args):
        ...


class InfoLineSimple(InfoLine):

    def _check_if_valid(self):
        if '=' in self._line:
            raise Exception(f'Invalid {self.__class__.__name__}: {self._line}')

    def _save_info(self):
        pass

    def get_line(self):
        return self._line

    def set_value(self, *args, **kwargs):
        pass

    def get_value(self):
        return self._line.strip('* ')


class InfoLineEditable(InfoLine):

    def _check_if_valid(self):
        if '=' not in self._line:
            raise Exception(f'Invalid {self.__class__.__name__}: {self._line}')

    def _save_info(self):
        self._key, self._value = [item.strip('* ') for item in self._line.split('=')]

    def get_line(self):
        return f'* {self._key} = {self._value}'

    def set_value(self, *args):
        self._value = args[0]

    def get_value(self):
        return self._value


class HeaderFormLine(ABC):

    def __init__(self, line: str, *args, **kwargs):
        self._line = line
        if ':' not in self._line:
            self._line = f'{self._line}:'
        self._match_string = kwargs.pop('match_string', self._line[:9])
        self._check_if_valid()
        self._save_info()

    def __str__(self):
        return self.get_line()

    @property
    def id(self):
        return self._line.split(':', 1)[0].strip()

    @property
    def data_string(self):
        return self.get_line().split(':', 1)[-1].strip()

    @data_string.setter
    def data_string(self, string: str):
        self._line = f'{self.key_string}: {string}'
        self._save_info()

    @property
    def key_string(self):
        return self.get_line().split(':', 1)[0].strip()

    @property
    def match_string(self):
        return self._match_string

    @abstractmethod
    def _check_if_valid(self):
        ...

    @abstractmethod
    def _save_info(self):
        ...

    @abstractmethod
    def get_line(self):
        ...

    @abstractmethod
    def set_value(self, *args, **kwargs):
        ...

    @abstractmethod
    def get_value(self, *args):
        ...

    @abstractmethod
    def get_all_values(self, *args):
        ...


class OneItemHeaderFormLine(HeaderFormLine):

    def __init__(self, *args, **kwargs):
        self._key = None
        self._value = None
        super().__init__(*args, **kwargs)

    def _check_if_valid(self):
        if '#' in self._line:
            raise Exception(f'Invalid {self.__class__.__name__}: {self._line.strip()}')

    def _save_info(self):
        self._key, self._value = [item.strip() for item in self._line.split(':')]

    def get_line(self):
        return f'{self._key}: {self._value}'

    def set_value(self, *args, **kwargs):
        for key, value in kwargs.items():
            key = strip_meta_key(key)
            if key.startswith(strip_meta_key(self.match_string)):
                self._value = str(value)
                return
        self._value = str(args[0])

    def get_value(self, *args):
        return self._value

    def get_all_values(self):
        return {self._key: self._value}


class MultipleItemHeaderFormLine(HeaderFormLine):

    def __init__(self, *args, **kwargs):
        self._data = {}
        super().__init__(*args, **kwargs)

    def _check_if_valid(self):
        if '#' not in self._line:
            raise Exception(f'Invalid {self.__class__.__name__}: {self._line.strip()}')

    def _save_info(self):
        meta_string = self._line.split(':', 1)[-1].strip()
        self._data = utils.metadata_string_to_dict(meta_string)

    def get_line(self):
        return f'{self.id}: {utils.metadata_dict_to_string(self._data)}'

    def set_value(self, *args, **kwargs):
        for key, value in kwargs.items():
            meta = get_mapped_meta(key)
            self._data[meta] = value

    def get_value(self, *args):
        if len(args) == 1:
            return self._data.get(get_mapped_meta(args[0]))
        return_dict = {}
        for arg in args:
            meta = get_mapped_meta(arg)
            return_dict[meta] = self._data[meta]
        return return_dict

    def get_all_values(self):
        return self._data


def get_info_line_object(line: str, **kwargs):
    if not line.startswith('* '):
        raise f'Invalid info line: {line}'
    if '=' in line:
        return InfoLineEditable(line)
    return InfoLineSimple(line)


def get_header_form_line_object(line: str, **kwargs):
    if not line.startswith('** '):
        raise f'Invalid header form line: {line}'
    if '#' in line:
        return MultipleItemHeaderFormLine(line, **kwargs)
    return OneItemHeaderFormLine(line, **kwargs)


class HeaderFormFile:

    def __init__(self, file):
        self._cls = None
        if isinstance(file, HdrFile):
            self._cls = HdrFile
        elif isinstance(file, HexFile):
            self._cls = HexFile
        else:
            msg = f'{file} is not a valid {self.__class__.__name__}'
            logger.error(msg)
            raise FileNotFoundError(msg)
        self._file = file
        self._lines = []

        self._lines_before = []
        self._header_form_lines = []
        self._lines_after = []
        self._header_form_lines_mapping = {}

        self._header_form_default_objects = []
        self._header_form_default_object_mapping = {}

        self._info_field_mapping = {}

        self._load_header_form_default_objects()
        self._load_file()
        self._update_current_header()
        self._add_missing_nmea_fields()

    def _load_header_form_default_objects(self):
        for key, value in HEADER_FORM_KEYS.items():
            obj = get_header_form_line_object(key, match_string=value)
            if 'Metadata adm' in key:
                obj.set_value(**dict((meta, '') for meta in METADATA_ADMIN_LIST))
            elif 'Metadata con' in key:
                obj.set_value(**dict((meta, '') for meta in METADATA_CONDITIONS_LIST))
            elif 'Pumps' in key:
                obj.set_value(**dict((meta, '') for meta in PUMPS_LIST))
            elif 'EventID' in key:
                obj.set_value(**dict((meta, '') for meta in EVENT_IDS_LIST))
            self._header_form_default_objects.append(obj)
            for k, vi in obj.get_all_values().items():
                k = strip_meta_key(k)
                self._header_form_default_object_mapping[k] = obj

    def _load_file(self):
        self._lines = []
        with open(self.path) as fid:
            for line in fid:
                self._lines.append(line.strip())
        return self._lines

    @property
    def path(self):
        return self._file.path

    @property
    def header_lines(self) -> List[str]:
        return [line.strip() for line in self._lines if line.startswith(HEADER_FORM_PREFIX)]

    @property
    def header_fields(self) -> List[str]:
        return [line.split(':')[0].strip(' *') for line in self.header_lines]

    def _add_missing_nmea_fields(self) -> None:
        tot_string = '_'.join([obj.get_line() for obj in self._lines_before])
        missing = []
        for nmea in NMEA_FIELDS:
            if nmea not in tot_string:
                missing.append(get_info_line_object(nmea))
        if not missing:
            return

        new_lines_before = []
        for obj in self._lines_before:
            new_lines_before.append(obj)
            if obj.key_string == 'System UpLoad Time':
                new_lines_before.extend(missing)

    def _split_lines(self):
        """Split lines in file into self._header_lines, self._before_lines and self._after_lines"""
        self._lines_before = []
        self._header_form_lines = []
        self._lines_after = []
        for line in self._lines:
            if line.startswith(HEADER_FORM_PREFIX):
                obj = get_header_form_line_object(line)
                self._header_form_lines.append(obj)
                for k, v in obj.get_all_values().items():
                    k = strip_meta_key(k)
                    self._header_form_lines_mapping[k] = obj
            elif self._header_form_lines:
                self._lines_after.append(line)
            else:
                obj = get_info_line_object(line)
                self._lines_before.append(obj)
                self._info_field_mapping[obj.key_string] = obj

    def _merge_lines(self):
        lines_before = [str(obj) for obj in self._lines_before]
        header_lines = [str(obj) for obj in self._header_form_lines]
        self._lines = lines_before + header_lines + self._lines_after

    def _update_current_header(self):
        """Replaces the header form with new lines. Matching data is added to the updated header form"""
        self._split_lines()
        for key, default_obj in self._header_form_default_object_mapping.items():
            key = strip_meta_key(key)
            current_obj = self._header_form_lines_mapping.get(key)
            if not current_obj:
                fe_logger.log_metadata(f'Missing metadata post {key}', add=self.path)
                continue
            default_obj.set_value(**{f'{key}': current_obj.get_value(key)})

        self._set_header_lines_from_default()
        self._merge_lines()

    def _set_header_lines_from_default(self):
        self._header_form_lines = self._header_form_default_objects
        self._header_form_lines_mapping = self._header_form_default_object_mapping

    def save_file(self, directory, overwrite=False):
        output_path = Path(directory, self.path.name)
        if output_path.exists() and not overwrite:
            raise FileExistsError(output_path)
        self._merge_lines()
        with open(output_path, 'w') as fid:
            fid.write('\n'.join(self._lines))
        return self._cls(output_path)

    def get_metadata(self, item):
        item = strip_meta_key(item)
        print(f'{self._header_form_lines_mapping=}')
        obj = self._header_form_lines_mapping.get(item)
        if not obj:
            return None
            # raise Exception(f'Invalid metadata key: {item}')
        return obj.get_value(item)

    def set_metadata(self, key, value):
        print(f'{key=}     :     {value=}')
        if value in [None, False]:
            value = ''
        else:
            value = str(value)
        meta = strip_meta_key(key)
        obj = self._header_form_lines_mapping.get(meta)
        if not obj:
            raise KeyError(f'Invalid key to set: {key}')
        old_value = obj.get_value(meta)
        if value != old_value:
            fe_logger.log_metadata(f'Changing value for {get_mapped_meta(meta)}: {old_value} -> {value}', add=self.path, level='warning')
        obj.set_value(**{meta: value})

    def update_nmea(self):
        self._update_nmea_lat()
        self._update_nmea_lon()
        self._update_nmea_time()

    def _update_nmea_lat(self):
        obj = self._info_field_mapping['NMEA Latitude']
        if obj.get_value():
            return
        value = self._header_form_lines_mapping['latitude'].get_value()
        set_value = f'{value} N'
        obj.set_value(set_value)
        fe_logger.log_metadata(f'NMEA Latitude added', add=self.path)

    def _update_nmea_lon(self):
        obj = self._info_field_mapping['NMEA Longitude']
        if obj.get_value():
            return
        value = self._header_form_lines_mapping['longitude'].get_value()
        set_value = f'{value} E'
        obj.set_value(set_value)
        fe_logger.log_metadata(f'NMEA Longitude added', add=self.path)

    def _update_nmea_time(self):
        obj = self._info_field_mapping['NMEA UTC (Time)']
        source_obj = self._info_field_mapping['System UpLoad Time']
        if obj.get_value():
            return
        obj.set_value(source_obj.get_value())
        fe_logger.log_metadata(f'NMEA UTC (Time) added', add=self.path)

    def _read_lines(self, lines):
        self._old_header = []
        self._old_header_mapping = {}
        self._pre_lines = []
        self._header_lines = []
        self._post_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith(HEADER_FORM_PREFIX):
                self._old_header.append(line)
                self._old_header_mapping[line.split(':', 1)[0].strip(' *')] = line
                if 'metadata admin' in line.lower():
                    self._metadata_admin_index = len(self._old_header) - 1
                elif 'metadata conditions' in line.lower():
                    self._metadata_condition_index = len(self._old_header) - 1
            elif self._old_header:
                self._post_lines.append(line)
            else:
                self._pre_lines.append(line)
        self._header_lines = self._old_header[:]


def update_header_form_file(file, output_directory, overwrite_file=False, overwrite_data=False, **data):
    if not any([isinstance(file, HdrFile), isinstance(file, HexFile)]):
        raise Exception(f'Not a valid header file: {file}')
    obj = HeaderFormFile(file)
    for key, value in data.items():
        if obj.get_metadata(key) is None:
            continue
        if not overwrite_data and obj.get_metadata(key):
            continue
        if not value.strip():
            fe_logger.log_metadata('No value to set for key', add=key)
            continue
        obj.set_metadata(key, value)
    obj.update_nmea()

    return obj.save_file(output_directory, overwrite=overwrite_file)
