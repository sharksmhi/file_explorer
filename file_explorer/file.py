from pathlib import Path
from abc import ABC, abstractmethod
import datetime
import hashlib

from file_explorer.patterns import get_file_stem_match
from file_explorer import mapping
from file_explorer import utils


class InstrumentFile(ABC):
    path = None
    suffix = None
    _path_info = {}
    _attributes = {}
    _lines = None
    data = None

    def __init__(self, path, ignore_pattern=False):
        self.path = Path(path)
        self.ignore_pattern = ignore_pattern
        self._key = None
        self._path_info = {}
        self._attributes = {}
        self._load_file()
        self._fixup()
        self._save_info_from_file()

        self._attributes.update(self._path_info)
        self._attributes['suffix'] = self.suffix
        self._attributes['cruise'] = '00'
        self._attributes['datetime'] = self.datetime
        if self.datetime:
            self._attributes['date'] = self.datetime.strftime('%Y%m%d')
            self._attributes['time'] = self.datetime.strftime('%H%M')
        self._save_attributes()

    def _get_datetime(self):
        # Overwrite this in subclasses if needed
        return self._get_datetime_from_path()

    @property
    def datetime(self):
        return self._get_datetime()

    def _save_info_from_file(self):
        # Overwrite this in subclasses
        pass

    def _save_attributes(self):
        # Overwrite this in subclasses
        pass

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return self.__str__()

    def __call__(self, *keys, **kwargs):
        if not self.is_matching(**kwargs):
            return
        else:
            if len(keys) == 1:
                return self.attributes.get(keys[0], False)
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
    def name(self):
        return self.path.name

    @property
    def stem(self):
        return self.path.stem

    @property
    def pattern(self):
        pat = self.name_match.string.split('.')[0]
        if self._path_info.get('prefix'):
            pat = pat.lstrip(self._path_info.get('prefix'))
        if self._path_info.get('tail'):
            pat = pat.rstrip(self._path_info.get('tail'))
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

        name_match = get_file_stem_match(self.path.name)
        if name_match:
            self.name_match = name_match
            self._path_info.update(name_match.groupdict())
        elif not self.ignore_pattern:
            raise UnrecognizedFile(f'File {self.path} does not math any registered file patterns')

    def _get_datetime_from_path(self):
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

    def in_bbox(self, **kwargs):
        return utils.in_bbox(self, **kwargs)

    def is_matching(self, **kwargs):
        return utils.is_matching(self, **kwargs)


class UnrecognizedFile(Exception):
    pass