import datetime

from file_explorer import utils
import logging

import pathlib
logger = logging.getLogger(__name__)


class InvalidClassToCompare(Exception):
    pass


def _get_datetime(obj):
    if isinstance(obj, Package):
        return obj('datetime')
    elif isinstance(obj, datetime.datetime):
        return obj
    raise InvalidClassToCompare


class Operations:

    def __call__(self, *args, **kwargs):
        pass

    def __eq__(self, other):
        if self('datetime') == _get_datetime(other):
            return True
        return False

    def __lt__(self, other):
        if self('datetime') < _get_datetime(other):
            return True
        return False

    def __gt__(self, other):
        if self('datetime') > _get_datetime(other):
            return True
        return False

    def __le__(self, other):
        if self('datetime') <= _get_datetime(other):
            return True
        return False

    def __ge__(self, other):
        if self('datetime') >= _get_datetime(other):
            return True
        return False


class Package(Operations):
    """
    Class to hold several seabird files with the same filename structure.
    """
    INSTRUMENT_TYPE = 'sbe'
    RAW_FILES_EXTENSIONS = ['.bl', '.btl', '.hdr', '.hex', '.ros', '.xmlcon', '.con', '.xml']

    def __init__(self, attributes=None, old_key=False, **kwargs):
        self._files = []
        self._old_key = old_key
        self._config_file_suffix = None
        attributes = attributes or {}
        self._attributes = dict((key, value.lower()) for key, value in attributes.items())

    def __str__(self):
        if not self._files:
            return f'Empty {self.INSTRUMENT_TYPE} Package'
        string = f'Package({self.INSTRUMENT_TYPE}): {self.pattern}'
        for file_obj in sorted([str(f) for f in self._files]):
            string = string + '\n    ' + str(file_obj)
        return string

    def __call__(self, *keys, **kwargs):
        if not utils.is_matching(self, **kwargs):
            return
        else:
            if len(keys) == 1:
                return self.attributes.get(keys[0].lower(), False)
            return tuple([self.attributes.get(key.lower(), False) for key in keys])

    def __getitem__(self, item):
        return self.path(item)

    def __getattr__(self, item):
        return self(item)

    def in_bbox(self, **kwargs):
        return utils.in_bbox(self, **kwargs)

    def path(self, item):
        for f in self._files:
            if f.suffix[1:] == item or f.suffix == item:
                return f.path

    @property
    def pattern(self):
        if not self._files:
            return False
        return self._files[0].pattern.upper()

    @property
    def files(self):
        return self._files

    @property
    def file_names(self):
        return [file.name for file in self.files]

    @property
    def data(self):
        for file in self.files:
            if hasattr(file, 'data'):
                return file.data

    def get_data(self, **kwargs):
        for file_obj in self._files:
            if not utils.is_matching(file_obj, **kwargs):
                continue
            elif file_obj.data is not None:
                return file_obj.data

    @property
    def attributes(self):
        attributes = dict()
        attributes.update(self._attributes)
        attributes['config_file_suffix'] = self._config_file_suffix
        attributes['nr_files'] = len(self.files)
        if self.files:
            attributes['pattern'] = self.files[0].pattern
        for file_obj in self._files:
            for key, value in file_obj.attributes.items():
                if not value:
                    continue
                attributes[key] = value
        return attributes

    @property
    def key(self):
        if not all([value for key, value in self.key_info.items() if key != 'test']):
            return None
        if self._old_key:
            logger.warning(f'Using old file name structure')
            logger.debug(f"ship: {self('ship')}: {utils.get_internal_ship_code(self('ship'))}")
            logger.debug(str(self.key_info))
            parts = [self('instrument'),
                     self('instrument_number'),
                     self('datetime').strftime('%Y%m%d_%H%M'),
                     utils.get_internal_ship_code(self('ship')),
                     self('serno')]
        else:
            parts = [self('instrument'),
                     self('instrument_number'),
                     self('datetime').strftime('%Y%m%d_%H%M'),
                     self('ship'),
                     self('cruise') or '00',
                     self('serno')]
        test = self('test')
        if type(test) == str:
            parts.append(test)
        return '_'.join(parts).upper()

    @property
    def key_info(self):
        if self._old_key:
            return dict(instrument=self('instrument'),
                        instrument_number=self('instrument_number'),
                        datetime=self('datetime'),
                        ship=self('ship'),
                        serno=self('serno'),
                        test=self('test'))

        return dict(instrument=self('instrument'),
                    instrument_number=self('instrument_number'),
                    datetime=self('datetime'),
                    ship=self('ship'),
                    cruise=self('cruise') or '00',
                    serno=self('serno'),
                    test=self('test'))

    def add_file(self, file, replace=False):
        if file.name in self.file_names:
            return False
        elif self._files and file.pattern != self._files[0].pattern:
            return False

        if replace:
            for file in self._files:
                if file.get_proper_name() == file.get_proper_name():
                    self._files.pop(self._files.index(file))

        self._files.append(file)
        self._set_config_suffix(file)
        self.set_key()

    def _set_config_suffix(self, file):
        if 'con' in file.suffix:
            self._config_file_suffix = file.suffix

    def set_key(self):
        for file in self.files:
            file.key = self.key

    def get_files(self, **kwargs):
        matching_files = []
        for file in self._files:
            if all([file(key) == value for key, value in kwargs.items()]):
                matching_files.append(file)
        return matching_files

    def get_file(self, **kwargs):
        matching_files = self.get_files(**kwargs)
        if not matching_files:
            logger.error(self.key)
            raise Exception(f'No matching files for keyword arguments {kwargs}')
        if len(matching_files) > 1:
            raise Exception(f'To many matching files for keyword arguments {kwargs}: {matching_files}')
        return matching_files[0]

    def get_file_path(self, **kwargs):
        file = self.get_file(**kwargs)
        return file.path

    def get_file_paths(self):
        return [file.path for file in self.files]

    def get_raw_files(self):
        return [file for file in self._files if file.suffix in self.RAW_FILES_EXTENSIONS]

    def get_plot_files(self):
        return [file for file in self._files if file.suffix == '.jpg']

    def get_attributes_from_all_files(self):
        all_list = []
        for file in self.files:
            all_list.append(file.attributes.copy())
        return all_list

    def write_attributes_from_all_files(self, directory, transpose=False):
        all_list = self.get_attributes_from_all_files()
        header = set()
        for item in all_list:
            header.update(list(item.keys()))
        header = sorted(header)

        if transpose:
            lines = []
            for col in header:
                line = [col]
                for item in all_list:
                    value = str(item.get(col))
                    line.append(value)
                lines.append('\t'.join(line))
        else:
            lines = []
            lines.append('\t'.join(header))
            for item in all_list:
                line = []
                for col in header:
                    value = str(item.get(col))
                    line.append(value)
                lines.append('\t'.join(line))

        path = pathlib.Path(directory, f'attributes_{self.key}.txt')
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))


    def validate(self):
        """
        Validates the package. Making cross checks etc.
        :return:
        """
        skip_keys = ['tail', 'prefix', 'suffix', 'sensor_info']
        mismatch = {}
        attributes = {}
        for file in self._files:
            for key, value in file.attributes.items():
                if key in skip_keys:
                    continue
                if key not in attributes:
                    attributes[key] = (str(file), value)
                else:
                    if attributes[key][1] != value:
                        mismatch.setdefault(key, [attributes[key]])
                        mismatch[key].append((str(file), value))
        return mismatch


class MvpPackage(Package):
    INSTRUMENT_TYPE = 'mvp'
    RAW_FILES_EXTENSIONS = ['.eng', '.log', '.m1', '.raw', '.asc', '.asvp', '.calc', '.em1', '.rnn', '.s10', '.s12', '.s52']

    def _set_config_suffix(self, file):
        pass

    @property
    def key(self):
        if not all(list(self.key_info.values())):
            return None
        return '_'.join([self('instrument'),
                         self('date'),
                         self('time'),
                         self('transect')]).upper()

    @property
    def key_info(self):
        return dict(instrument=self('instrument'),
                    date=self('date'),
                    time=self('time'),
                    transect=self('transect'))


class OdvPackage(Package):
    INSTRUMENT_TYPE = 'odv'
    RAW_FILES_EXTENSIONS = []

    def _set_config_suffix(self, file):
        pass

    @property
    def key(self):
        if not all(list(self.key_info.values())):
            return None
        return '_'.join([self('instrument'),
                         self('date'),
                         self('time'),
                         self('transect')]).upper()

    @property
    def key_info(self):
        return dict(instrument=self('instrument'),
                    date=self('date'),
                    time=self('time'),
                    transect=self('transect'))


class PrsPackage(Package):
    INSTRUMENT_TYPE = 'prs'
    RAW_FILES_EXTENSIONS = []

    def _set_config_suffix(self, file):
        pass

    @property
    def key(self):
        if not all([value for value in self.key_info.values()]):
            return None
        parts = [self('datetime').strftime('%Y%m%d_%H%M'),
                 self('ship'),
                 self('cruise') or '00',
                 self('serno')]
        test = self('test')
        if type(test) == str:
            parts.append(test)
        return '_'.join(parts).upper()

    @property
    def key_info(self):
        return dict(datetime=self('datetime'),
                    ship=self('ship'),
                    cruise=self('cruise') or '00',
                    serno=self('serno'))



