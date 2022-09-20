import datetime
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
import logging
import xml

from file_explorer import mapping
from file_explorer import utils
from file_explorer.patterns import get_file_name_match

logger = logging.getLogger(__name__)


class InstrumentFile(ABC):
    suffix = None
    _path_info = {}
    _attributes = {}
    _lines = None
    package_instrument_type = None
    encoding = 'cp1252'

    def __init__(self, path, ignore_pattern=False, **kwargs):
        self._path = Path(path)
        self.ignore_pattern = ignore_pattern
        self._key = None
        self._path_info = {}
        self._attributes = {}
        self._no_datetime_from_file_name = kwargs.pop('no_datetime_from_file_name', False)

        encoding_key = f'{self.suffix[1:]}_encoding'
        self.encoding = kwargs.get(encoding_key) or self.encoding

        self.edit_mode = kwargs.get('edit_mode', False)

        try:
            self._load_file()
            self._fixup()
            self._save_info_from_file()

            self._attributes.update(self._path_info)
            self._attributes['suffix'] = self.suffix
            self._attributes['path'] = str(self.path)
            self._attributes['name'] = self.name
            # self._attributes['cruise'] = '00'
            self._save_attributes()
            self._add_and_map_attributes()
        except xml.etree.ElementTree.ParseError as e:
            logger.error(f'Could not parse xml in file: {self.path}\n{e}')
            print(self.path)
            raise

    def _get_datetime(self):
        # Overwrite this in subclasses if needed
        return self._get_datetime_from_path()

    @property
    def datetime(self):
        return self._get_datetime()

    @abstractmethod
    def _save_info_from_file(self):
        # Overwrite this in subclasses
        pass

    @abstractmethod
    def _save_attributes(self):
        # Overwrite this in subclasses
        pass

    def validate(self, case_sensitive=True):
        return {}

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return self.__str__()

    def __call__(self, *keys, **kwargs):
        if not utils.is_matching(self, **kwargs):
            return
        else:
            if len(keys) == 1:
                return self.attributes.get(keys[0].lower(), False)
            return tuple([self.attributes.get(key.lower(), False) for key in keys])

    def __getattr__(self, item):
        return self(item)

    def __eq__(self, other):
        if self.md5 == other.md5:
            return True
        return False

    @property
    def lines(self):
        """
        Use in self.save_file
        """
        return self._lines

    @lines.setter
    def lines(self, lines):
        if not isinstance(lines, list):
            raise TypeError(f'Invalid type when setting lines in file: {self}')
        self._lines = lines

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, key):
        self._key = key

    @property
    def path(self):
        return self._path

    @property
    def name(self):
        return self.path.name

    @property
    def stem(self):
        return self.path.stem

    @property
    def pattern(self):
        pat = self.name_match.string.split('.')[0]
        prefix = self._path_info.get('prefix')
        tail = self._path_info.get('tail')
        if prefix and pat.startswith(prefix):
            pat = pat[len(prefix):]
        if tail and pat.endswith(tail):
            pat = pat[:-len(tail)]


        # if self._path_info.get('prefix'):
        #     pat = pat.lstrip(self._path_info.get('prefix'))
        # if self._path_info.get('tail'):
        #     pat = pat.rstrip(self._path_info.get('tail'))
        return pat.upper()

    @property
    def attributes(self):
        return self._attributes

    @property
    def md5(self):
        with open(self.path, 'rb') as fid:
            return hashlib.md5(fid.read()).hexdigest()

    def _load_file(self):
        if self.path.suffix.lower() != self.suffix.lower():
            raise UnrecognizedFile(f'{self.path} does not have suffix {self.suffix}')

        name_match = get_file_name_match(self.path.name)
        if name_match:
            self.name_match = name_match
            self._path_info.update(name_match.groupdict())
        elif not self.ignore_pattern:
            raise UnrecognizedFile(f'File {self.path} does not match any '
                                   f'registered file patterns')

    def _get_datetime_from_path(self, force=False):
        if self._no_datetime_from_file_name and not force:
            return
        if all([self._path_info.get(key) for key in ['year', 'day', 'month', 'hour', 'minute', 'second']]):
            return datetime.datetime(int(self._path_info['year']),
                                     int(self._path_info['month']),
                                     int(self._path_info['day']),
                                     int(self._path_info['hour']),
                                     int(self._path_info['minute']),
                                     int(self._path_info['second']))
        elif all([self._path_info.get(key) for key in ['year', 'day', 'month', 'hour', 'minute']]):
            return datetime.datetime(int(self._path_info['year']),
                                     int(self._path_info['month']),
                                     int(self._path_info['day']),
                                     int(self._path_info['hour']),
                                     int(self._path_info['minute']))
        elif all([self._path_info.get(key) for key in ['year', 'day', 'month']]):
            return datetime.datetime(int(self._path_info['year']),
                                     int(self._path_info['month']),
                                     int(self._path_info['day']))

    def _fixup(self):
        if self._path_info:
            self._path_info['year'] = mapping.get_year_mapping(self._path_info.get('year'))
            if 'ship' in self._path_info:
                self._path_info['ship'] = mapping.get_ship_mapping(self._path_info['ship'])
            if self._path_info.get('serno'):
                self._path_info['serno'] = self._path_info['serno'].zfill(4)

    def _add_and_map_attributes(self):
        self._attributes['datetime'] = self.datetime
        if self.datetime:
            self._attributes['date'] = self.datetime.strftime('%Y-%m-%d')
            self._attributes['time'] = self.datetime.strftime('%H:%M')
        if self._attributes.get('ship'):
            self._attributes['ship'] = mapping.get_ship_mapping(self._attributes['ship'])
        if self._attributes.get('additional sampling'):
            self._attributes['add_smp'] = self._attributes.get('additional sampling')
        if self._attributes.get('instrument') and self._attributes.get('instrument_number'):
            self._attributes['instrument_serie'] = self._attributes.get('instrument_number')
            self._attributes['instrument_id'] = f"{self._attributes.get('instrument')}{self._attributes.get('instrument_number')}".upper()

    def get_proper_name(self):
        prefix = self('prefix') or ''
        tail = self('tail') or ''
        return f'{prefix + self.key + tail}{self.suffix}'

    def get_proper_path(self, directory=None):
        if not directory:
            directory = self.path.parent
        return Path(directory, self.get_proper_name())

    def get_save_name(self):
        return self.get_proper_name()

    def get_save_path(self, directory=None):
        if not directory:
            directory = self.path.parent
        return Path(directory, self.get_save_name())

    def save_file(self, directory=None, overwrite=False):
        if not self.lines:
            return
        target_path = self.get_save_path(directory)
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        with open(target_path, 'w') as fid:
            fid.write('\n'.join(self.lines))
        return target_path


class UnrecognizedFile(Exception):
    pass

