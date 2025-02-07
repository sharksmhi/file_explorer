import datetime
import logging
import pathlib
import socket
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from file_explorer import exceptions
from file_explorer.file import InstrumentFile
from file_explorer.file_explorer_logger import fe_logger
from file_explorer.seabird import utils
from file_explorer.seabird.btl_file import BtlFile
from file_explorer.seabird.hdr_file import HdrFile
from file_explorer.seabird.hex_file import HexFile
from file_explorer.seabird.ros_file import RosFile
from file_explorer.seabird.xml_file import XmlFile

logger = logging.getLogger(__name__)

LIMS_SHIP_MAPPING = {'77SE': '7710',
                     '7710': '7710'}

HEADER_FORM_PREFIX = '**'
INFO_LINE_PREFIX = '*'

HEADER_FORM_KEYS = {
                '** Station:': '** Sta',
                '** Operator:': '** Ope',
                '** Ship:': '** Shi',
                '** Cruise:': '** Cru',
                # '** Latitude [GG MM.mm N]:': '** Lat',
                # '** Longitude [GGG MM.mm E]:': '** Lon',
                '** Latitude:': '** Lat',
                '** Longitude:': '** Lon',
                '** Pumps: #': '** Pum',
                '** EventIDs: #': '** Eve',
                '** Additional Sampling:': '** Add',
                '** Metadata admin: #': '** Metadata adm',
                '** Metadata conditions: #': '** Metadata con',
                #'** LIMS Job:': '** LIM',
                '** Bottom Depth [m]:': '** Bottom Depth',
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
    # 'Latitude',
    # 'Longitude',
    'Pumps',
    'EventIDs',
    'Additional Sampling',
    'Metadata admin',
    'Metadata conditions',
    #'LIMS Job',
    'Bottom Depth [m]',
    'File modified programmatically',
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
    'WINSP',
    'WINDIR',
    'AIRPRES',
    'AIRTEMP',
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
        # if not line.startswith('*'):
        #     raise Exception(f'Invalid {self.__class__.__name__}: {line}')
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


class InfoLineNoPrefix(InfoLine):

    def _check_if_valid(self):
        if self._line.startswith('*'):
            raise Exception(f'Invalid {self.__class__.__name__}: {self._line}')

    def _save_info(self):
        pass

    def get_line(self):
        return self._line

    def set_value(self, *args, **kwargs):
        pass

    def get_value(self):
        return self._line


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
        self._key, self._value = [item.strip('* ') for item in self._line.split('=', 1)]

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
        if self._line.count(':') > 1:
            raise exceptions.InvalidHeaderFormLine(f'To many : in line ({self._line})')
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


def get_info_line_object(line: str, **kwargs) -> InfoLine:
    if line.startswith(INFO_LINE_PREFIX):
        if '=' in line:
            return InfoLineEditable(line)
        return InfoLineSimple(line)
    else:
        return InfoLineNoPrefix(line)


def get_header_form_line_object(line: str, **kwargs):
    if not line.startswith('** '):
        raise Exception(f'Invalid header form line: {line}')
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
        elif isinstance(file, RosFile):
            self._cls = RosFile
        elif isinstance(file, BtlFile):
            self._cls = BtlFile
        elif isinstance(file, XmlFile):
            self._cls = XmlFile
        else:
            msg = f'{file} is not a valid {self.__class__.__name__}'
            logger.error(msg)
            raise FileNotFoundError(msg)
        self._file = file
        self._lines = []

        self._lines_before: list[InfoLine] = []
        self._header_form_lines: list[HeaderFormLine] = []
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

    @property
    def nmea_latitude(self) -> str:
        return self._info_field_mapping['NMEA Latitude'].get_value()

    @property
    def nmea_longitude(self) -> str:
        return self._info_field_mapping['NMEA Longitude'].get_value()

    def print_header_form(self) -> None:
        print('=' * 100)
        print(f'Header lines for file: {self.path}')
        print('-' * 100)
        for line in self._header_form_lines:
            print(line)
        print('=' * 100)

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
                self._add_header_form_line(line)
            elif self._header_form_lines:
                self._lines_after.append(line)
            else:
                obj = get_info_line_object(line)
                self._lines_before.append(obj)
                self._info_field_mapping[obj.key_string] = obj

    def _add_header_form_line(self, line: str):
        obj = get_header_form_line_object(line)
        self._header_form_lines.append(obj)
        for k, v in obj.get_all_values().items():
            k = strip_meta_key(k)
            self._header_form_lines_mapping[k] = obj

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
        obj = self._header_form_lines_mapping.get(item)
        if not obj:
            return None
            # raise Exception(f'Invalid metadata key: {item}')
        return obj.get_value(item)

    def has_metadata(self, key: str) -> bool:
        meta = strip_meta_key(key)
        if meta in self._header_form_lines_mapping:
            return True
        return False

    def set_metadata(self, key, value):
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

    # def set_lims_job(self, data: dict):
    #     year = data.get('year')
    #     ship = data.get('ship')
    #     serno = data.get('serno')
    #     if not all([year, ship, serno]):
    #         fe_logger.log_metadata(f'Missing information to set LIMS Job', add=f'{year=}, {ship=}, {serno=}',
    #                                level='warning')
    #         return
    #
    #     key = 'LIMS Job:'
    #
    #     ship = LIMS_SHIP_MAPPING.get(ship)
    #     if ship is None:
    #         fe_logger.log_metadata(f'Could not map SHIP to set LIMS Job', add=ship,
    #                                level='warning')
    #         return
    #
    #     lims_job_string = f"{key} {year}{ship}-{serno}"
    #
    #     current_value = self.get_metadata('LIMS Job')
    #     if current_value != lims_job_string:
    #         self.set_metadata('LIMS Job', lims_job_string)
    #         return True
    #     return False

    def set_bottom_depth(self, depth: str):
        current_value = self.get_metadata('bottom')
        if current_value != depth:
            self.set_metadata('bottom', depth)
            return True
        return False

    def add_modified_message(self):
        time_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        line = f'** File modified programmatically: by {pathlib.Path.home().name} on {socket.gethostname()} {time_str}'
        self._add_header_form_line(line)

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


class old_HeaderFormFile:

    def __init__(self, file):
        self._cls = None
        if isinstance(file, HdrFile):
            self._cls = HdrFile
        elif isinstance(file, HexFile):
            self._cls = HexFile
        if isinstance(file, RosFile):
            self._cls = RosFile
        elif isinstance(file, BtlFile):
            self._cls = BtlFile
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
        obj = self._header_form_lines_mapping.get(item)
        if not obj:
            return None
            # raise Exception(f'Invalid metadata key: {item}')
        return obj.get_value(item)

    def set_metadata(self, key, value):
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


def update_header_form_file(file: InstrumentFile, output_directory, overwrite_file=False, **data):
    def mod_pos(pos: str) -> str:
        pos = pos.rstrip('NEWS').lstrip('0').strip()
        return pos

    is_mod = False
    obj = HeaderFormFile(file)
    fe_logger.log_metadata(f'Metadata given to {file.path}', add=str(data), level=fe_logger.DEBUG)
    for key, value in data.items():
        lower_key = key.lower().strip()
        val = value.strip()
        current_value = obj.get_metadata(key)
        if current_value is None:
            continue
        current_value = current_value.strip()
        if not val:
            fe_logger.log_metadata('No value to set for key', add=key, level=fe_logger.WARNING)
            continue
        if lower_key == 'station' and val:
            obj.set_metadata(key, val)
            if val != current_value:
                is_mod = True
        elif lower_key == 'ship':
            obj.set_metadata(key, val)
            if val != current_value:
                is_mod = True
        elif lower_key == 'additional sampling':
            obj.set_metadata(key, val)
            if val != current_value:
                is_mod = True
        elif lower_key in ['mprog', 'slabo', 'alabo', 'refsk']:
            obj.set_metadata(key, val)
            if val != current_value:
                is_mod = True
        elif lower_key == 'cruise':
            if val:
                obj.set_metadata(key, val)
                if val != current_value:
                    is_mod = True
        elif lower_key == 'latitude':
            pos_val = f'{val} N'
            if not obj.nmea_latitude.strip():
                fe_logger.log_metadata('Missing NMEA Latitude', add=str(file.path), level=fe_logger.WARNING)
            if not current_value:
                fe_logger.log_metadata('Latitude is missing in file. Adding!', add=str(file.path))
                obj.set_metadata(key, pos_val)
                if val != current_value:
                    is_mod = True
            elif mod_pos(current_value) != mod_pos(current_value):
                fe_logger.log_metadata('Latitude in file differs from given metadata. LOOK IT UP!', add=str(file.path), level=fe_logger.ERROR)
            else:
                obj.set_metadata(key, pos_val)
                if val != current_value:
                    is_mod = True
        elif lower_key == 'longitude':
            pos_val = f'{val} E'
            if not obj.nmea_longitude.strip():
                fe_logger.log_metadata('Missing NMEA Longitude', add=str(file.path), level=fe_logger.WARNING)
            if not current_value:
                fe_logger.log_metadata('Longitude is missing in file. Adding!', add=str(file.path))
                obj.set_metadata(key, pos_val)
                if val != current_value:
                    is_mod = True
            elif mod_pos(current_value) != mod_pos(current_value):
                fe_logger.log_metadata('Longitude in file differs from given metadata. LOOK IT UP!', add=str(file.path), level=fe_logger.ERROR)
            else:
                obj.set_metadata(key, pos_val)
                if val != current_value:
                    is_mod = True
        elif key == 'event_id':
            if not current_value:
                obj.set_metadata(key, val)
                if val != current_value:
                    is_mod = True
            elif current_value != val:
                fe_logger.log_metadata('EVENT_ID is different!', level=fe_logger.ERROR, add=str(file.path))
        elif key == 'parent_event_id':
            if not current_value:
                obj.set_metadata(key, val)
                if val != current_value:
                    is_mod = True
            elif current_value != val:
                fe_logger.log_metadata('PARENT_EVENT_ID is different!', level=fe_logger.ERROR, add=str(file.path))
        elif obj.has_metadata(key):
            obj.set_metadata(key, val)

    # modified = obj.set_lims_job(data=data)
    # if modified:
    #     is_mod = True
    modified = obj.set_bottom_depth(data.get('WADEP'))
    if modified:
        is_mod = True

    if is_mod:
        obj.add_modified_message()
        # obj.set_metadata(key, value)
    # obj.update_nmea()

    return obj.save_file(output_directory, overwrite=overwrite_file)


def old_update_header_form_file(file, output_directory, overwrite_file=False, overwrite_data=False, **data):
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
    # obj.update_nmea()

    return obj.save_file(output_directory, overwrite=overwrite_file)
