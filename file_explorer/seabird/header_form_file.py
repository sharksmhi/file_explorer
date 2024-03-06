from pathlib import Path
import logging
import re
from abc import ABC, abstractmethod

from typing import List

from file_explorer.seabird.hdr_file import HdrFile
from file_explorer.seabird.hex_file import HexFile

from file_explorer.seabird import utils
from file_explorer.logger import file_explorer_logger


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


def strip_meta_key(meta):
    return meta.strip('* :').lower().split()[0]


META_MAPPING = {strip_meta_key(key): key for key in HEADER_FIELDS + METADATA_ADMIN_LIST + METADATA_CONDITIONS_LIST + PUMPS_LIST + EVENT_IDS_LIST}


def get_mapped_meta(key):
    return META_MAPPING[strip_meta_key(key)]


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
        # print(f'{args=}    :    {kwargs=}')
        # print()
        # print('-'*100)
        for key, value in kwargs.items():
            meta = get_mapped_meta(key)
            # print(f'{key=}   :   {meta=}   :   {value=}')
            self._data[meta] = value
            # print(f'{id(self._data)}: {self._data=}')

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

        self._load_header_form_default_objects()
        self._load_file()
        self._update_current_header()

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
    def header_lines(self) -> List[str]:
        return [line.strip() for line in self._lines if line.startswith(HEADER_FORM_PREFIX)]

    @property
    def header_fields(self) -> List[str]:
        return [line.split(':')[0].strip(' *') for line in self.header_lines]

    def _split_lines(self):
        """Split lines in file into self._header_lines, self._before_lines and self._after_lines"""
        self._lines_before = []
        self._header_form_lines = []
        self._lines_after = []
        for line in self._lines:
            if line.startswith('**'):
                obj = get_header_form_line_object(line)
                self._header_form_lines.append(obj)
                for k, v in obj.get_all_values().items():
                    k = strip_meta_key(k)
                    self._header_form_lines_mapping[k] = obj
            elif self._header_form_lines:
                self._lines_after.append(line)
            else:
                self._lines_before.append(line)

    def _merge_lines(self):
        header_lines = [str(obj) for obj in self._header_form_lines]
        self._lines = self._lines_before + header_lines + self._lines_after

    def _update_current_header(self):
        """Replaces the header form with new lines. Matching data is added to the updated header form"""
        self._split_lines()
        for key, default_obj in self._header_form_default_object_mapping.items():
            key = strip_meta_key(key)
            current_obj = self._header_form_lines_mapping.get(key)
            if not current_obj:
                file_explorer_logger.log_metadata(f'Missing metadata post {key}', add=self.path)
                continue
            # print(f'{key=}')
            default_obj.set_value(**{f'{key}': current_obj.get_value(key)})

        # for obj in self._header_form_default_objects:
        #     for current_obj in self._header_form_lines:
        #         if current_obj.id.startswith(obj.match_string):
        #             obj.set_value(**current_obj.get_all_values())
        #             break
        # self._header_form_lines = self._header_form_default_objects
        self._set_header_lines_from_default()
        self._merge_lines()

    def _set_header_lines_from_default(self):
        self._header_form_lines = self._header_form_default_objects
        self._header_form_lines_mapping = self._header_form_default_object_mapping

    def save_file(self, directory, overwrite=False):
        proj = self.get_metadata('proj')
        # print(f'C: {proj=}')
        output_path = Path(directory, self.path.name)
        if output_path.exists() and not overwrite:
            raise FileExistsError(output_path)
        self._merge_lines()
        proj = self.get_metadata('proj')
        # print(f'D: {proj=}')
        with open(output_path, 'w') as fid:
            fid.write('\n'.join(self._lines))
        return self._cls(output_path)

    # def __getitem__(self, item):
    #     item = strip_meta_key(item)
    #     obj = self._header_form_lines_mapping.get(item)
    #     if not obj:
    #         raise Exception(f'Invalid metadata key: {item}')
    #     return obj.get_value(item)

    # def __setitem__(self, key, value):
    #     if value in [None, False]:
    #         value = ''
    #     else:
    #         value = str(value)
    #     meta = strip_meta_key(key)
    #     obj = self._header_form_lines_mapping.get(meta)
    #     if not obj:
    #         raise KeyError(f'Invalid key to set: {key}')
    #     print()
    #     print(f'==: {meta=}   :   {value=}')
    #     print(f'{obj=}', str(obj))
    #     obj.set_value(**{meta: value})

    def get_metadata(self, item):
        item = strip_meta_key(item)
        obj = self._header_form_lines_mapping.get(item)
        if not obj:
            raise Exception(f'Invalid metadata key: {item}')
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
        # print()
        # print(f'A: {meta=}   :   {value=}')
        # print(f'{obj=}', str(obj))
        proj = obj.get_value('proj')
        # print(f'E: {proj=}')
        obj.set_value(**{meta: value})
        proj = obj.get_value('proj')
        # print(f'F: {proj=}')
        proj = self.get_metadata('proj')
        # print(f'G: {proj=}')

    # def __str__(self):
    #     self._merge_lines()
    #     sep_length = 130
    #     lines = []
    #     lines.append('-'*sep_length)
    #     lines.append(f'Header information in file: {self.path}')
    #     lines.append('-'*sep_length)
    #     lines.extend([item.strip() for item in self._lines])
    #     lines.append('-'*sep_length)
    #     return '\n'.join(lines)

    @property
    def path(self):
        return self._file.path

    def remove_header_line(self, match_string):
        lines = self._get_lines_from_file()
        new_lines = []
        for line in lines:
            if not line.startswith('**'):
                new_lines.append(line)
                continue
            if re.match(match_string, line):
                continue
            new_lines.append(line)
        self._read_lines(new_lines)

    def _read_lines(self, lines):
        self._old_header = []
        self._old_header_mapping = {}
        self._pre_lines = []
        self._header_lines = []
        self._post_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('**'):
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
        else:
            msg = f'{file} is not a valid {self.__class__.__name__}'
            logger.error(msg)
            raise FileNotFoundError(msg)
        self._file = file

        self._old_header = []
        self._old_header_mapping = {}

        self._pre_lines = []
        self._header_lines = []
        self._post_lines = []

        self._metadata_admin_index = None
        self._metadata_condition_index = None

        self._header_fields_added = False
        self._load_file()

    def _load_file(self):
        self._read_lines_from_file()
        self._add_header_fields()

    def __getitem__(self, item):
        item = item.upper()
        for line in self._header_lines:
            if item not in line.upper():
                continue
            for key, value in utils.get_dict_from_header_form_line(line).items():
                if key.upper() == item:
                    return value

    def __setitem__(self, key, value):
        if value in [None, False]:
            value = ''
        else:
            value = str(value)
        self._add_header_fields()
        key = key.upper()

        if key in METADATA_ADMIN_LIST:
            line = self._header_lines[self._metadata_admin_index]
            par, item_str = line.split(':', 1)
            items = utils.metadata_string_to_dict(item_str)
            items[key] = value
            self._header_lines[self._metadata_admin_index] = f'** Metadata admin: ' \
                                                             f'{utils.metadata_dict_to_string(items)}'
            logger.debug(f'{key} is set to {value}')
            return

        if key in METADATA_CONDITIONS_LIST:
            line = self._header_lines[self._metadata_condition_index]
            par, item_str = line.split(':', 1)
            items = utils.metadata_string_to_dict(item_str)
            items[key] = value
            self._header_lines[self._metadata_condition_index] = f'** Metadata conditions: ' \
                                                                 f'{utils.metadata_dict_to_string(items)}'
            logger.debug(f'{key} is set to {value}')
            return

        for i, line in enumerate(self._header_lines):
            if key not in line.upper():
                continue

            par, info_str = [item.strip() for item in line.split(':', 1)]
            par = par.strip(' *')
            if par.upper() == key:
                new_line = f'** {par}: {value}'
                self._header_lines[i] = new_line
                logger.debug(f'{key} is set to {value}')
                return
        logger.warning(f'No such key to set: {key}')

    def __str__(self):
        sep_length = 130
        lines = []
        lines.append('-'*sep_length)
        lines.append(f'Header information in file: {self.path}')
        lines.append('-'*sep_length)
        lines.extend([item.strip() for item in self.header_lines])
        lines.append('-'*sep_length)
        return '\n'.join(lines)

    @property
    def path(self):
        return self._file.path

    @property
    def pre_lines(self):
        return self._pre_lines

    @property
    def header_lines(self):
        return self._header_lines

    @property
    def post_lines(self):
        return self._post_lines

    @property
    def all_lines(self):
        all_lines = []
        all_lines.extend(self.pre_lines)
        all_lines.extend(self.header_lines)
        all_lines.extend(self.post_lines)
        return all_lines

    def remove_header_line(self, match_string):
        lines = self._get_lines_from_file()
        new_lines = []
        for line in lines:
            if not line.startswith('**'):
                new_lines.append(line)
                continue
            if re.match(match_string, line):
                continue
            new_lines.append(line)
        self._read_lines(new_lines)

    def _read_lines_from_file(self):
        lines = self._get_lines_from_file()
        self._read_lines(lines)

    def _get_lines_from_file(self):
        lines = []
        with open(self.path) as fid:
            for line in fid:
                lines.append(line)
        return lines

    def _read_lines(self, lines):
        self._old_header = []
        self._old_header_mapping = {}
        self._pre_lines = []
        self._header_lines = []
        self._post_lines = []
        for line in lines:
            line = line.strip()
            if line.startswith('**'):
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

    def _add_header_fields(self):
        """
        Adds all default header fields (rows).
        """
        if self._header_fields_added:
            return
        old_header = self._old_header[:]
        new_header = []
        for field in HEADER_FIELDS:
            present_value = self._old_header_mapping.get(field)
            if present_value:
                new_header.append(self._get_enriched_header_field(present_value))
                old_header.pop(old_header.index(present_value))
            else:
                value = f'** {field}: '
                new_header.append(self._get_enriched_header_field(value))

        new_header.extend(old_header)
        self._header_lines = new_header

        self._metadata_admin_index = HEADER_FIELDS.index('Metadata admin')
        self._metadata_condition_index = HEADER_FIELDS.index('Metadata conditions')
        self._header_fields_added = True

    @staticmethod
    def _get_enriched_header_field(current_line):
        """ Enrich the given header field with default data. Also cleans the data from unwanted spaces. """
        key, value = current_line.split(':', 1)
        lower_key = key.lower()
        if 'pumps' in lower_key:
            default_dict = dict((k, '') for k in PUMPS_LIST)
        elif 'event' in lower_key:
            default_dict = dict((k, '') for k in EVENT_IDS_LIST)
        elif 'admin' in lower_key:
            default_dict = dict((k, '') for k in METADATA_ADMIN_LIST)
        elif 'conditions' in lower_key:
            default_dict = dict((k, '') for k in METADATA_CONDITIONS_LIST)
        else:
            return f'{key.strip()}: {value.strip()}'
        if '#' in value:
            value_dict = utils.metadata_string_to_dict(value)
            default_dict.update(value_dict)
        return f'{key}: {utils.metadata_dict_to_string(default_dict)}'

    def save_file(self, directory, overwrite=False):
        output_path = Path(directory, self.path.name)
        if output_path.exists() and not overwrite:
            raise FileExistsError(output_path)

        with open(output_path, 'w') as fid:
            fid.write('\n'.join(self.all_lines))

        return self._cls(output_path)


def update_header_form_file(file, output_directory, overwrite_file=False, overwrite_data=False, **data):
    if not any([isinstance(file, HdrFile), isinstance(file, HexFile)]):
        raise Exception(f'Not a valid header file: {file}')
    obj = HeaderFormFile(file)
    proj = obj.get_metadata('proj')
    # print(f'A: {proj=}')
    for key, value in data.items():
        if not overwrite_data and obj.get_metadata(key):
            continue
        obj.set_metadata(key, value)
        proj = obj.get_metadata('proj')
        # print(f'B: {proj=}')
    # return obj
    return obj.save_file(output_directory, overwrite=overwrite_file)
