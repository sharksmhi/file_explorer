import pathlib
import os
import logging
import yaml

from . import watcher
from .exceptions import RootDirectoryNotSetError


logger = logging.getLogger(__name__)


class FileHandler:

    def __init__(self, config: dict, *args, **kwargs):
        """
        Structure for paths is:
        {
        root_key: {
                  sub_key: {
                            rel_path: sub_path (as string)
                            suffixes: [] (all if empty)
                            }
                  }
        }
        """
        self._config = config
        self._root_dirs = dict()
        self._files = dict()
        self._watchers = dict()
        self._year = None
        self._monitor_callbacks = []

    def __repr__(self):
        return f'{self.__class__.__name__} with root keys: {", ".join(self.root_keys)}'

    def __str__(self):
        lines = []
        lines.append(f'{self.__class__.__name__} with paths:')
        lines.append('-'*100)
        for root_key in sorted(self.root_keys):
            lines.append(str(self._root_dirs[root_key]))
            for sub_key in sorted(self.get_sub_keys(root_key)):
                lines.append(f'   {sub_key}')
        lines.append('-' * 100)
        return '\n'.join(lines)

    def __call__(self, root_key, sub_key=None):
        if sub_key:
            return self.get_dir(root_key, sub_key)
        return self.get_root_dir(root_key)

    @classmethod
    def from_yaml(cls, path):
        with open(path) as fid:
            data = yaml.safe_load(fid)
        return cls(data)

    @property
    def year(self):
        return self._year

    @property
    def root_keys(self):
        return list(self._config)

    def root_dir_is_set(self, root_key):
        try:
            self._check_root_dir(root_key)
            return True
        except RootDirectoryNotSetError:
            return False

    def _check_root_key(self, root_key: str):
        if root_key not in self.root_keys:
            raise KeyError(f'Invalid root_key: {root_key}')
        return True

    def _check_root_dir(self, root_key):
        self._check_root_key(root_key)
        if root_key not in self._root_dirs:
            msg = f'Root directory is not set for root _key: {root_key}'
            logger.warning(msg)
            raise RootDirectoryNotSetError(msg)
        root_dir = self._root_dirs[root_key]
        if not root_dir.exists():
            raise Exception(f'Root directory does not exist: {root_dir}')

    def _check_sub_key(self, root_key: str, sub_key: str):
        if sub_key not in self.get_sub_keys(root_key):
            raise KeyError(f'sub_key "{sub_key}" is not valid for root_key "{root_key}"')

    def get_sub_keys(self, root_key: str):
        self._check_root_key(root_key)
        return list(self._config.get(root_key))

    def set_year(self, year):
        """Set year will replace tag <YEAR> in all paths"""
        year = str(year).strip().lstrip('0')
        assert year.isdigit()
        assert len(year) == 4
        self._year = int(year)

    def set_root_dir(self, root_key, path):
        """Sets the root directory for the given root_key"""
        if not path:
            logger.warning(f'No valif path given to set root directory {root_key}: {path}')
            return
        path = pathlib.Path(path)
        if path.is_file():
            raise Exception(f'Can not set a file path as root directory: {path}')
        if not path.exists():
            raise Exception(f'Can not set a root path that not exist: {path}')
        self._check_root_key(root_key)
        if self._files.get(root_key) != path:
            self._reset_files(root_key)
        self._root_dirs[root_key] = path

    def _reset_files(self, root_key):
        self._files[root_key] = {}

    def get_root_dir(self, root_key):
        self._check_root_dir(root_key)
        return self._root_dirs[root_key]

    def _get_path(self, root_key: str, sub_key: str):
        self._check_sub_key(root_key, sub_key)
        sub_path = self._config.get(root_key).get(sub_key).get('rel_path')
        if sub_path is None or type(sub_path) != str:
            raise TypeError(f'"{sub_path}" is not a valid sub_path')
        if '<YEAR>' in sub_path and self.year is None:
            raise Exception(f'Year is not set to build path: {sub_path}')
        sub_path = sub_path.replace('<YEAR>', str(self.year))
        root_dir = self.get_root_dir(root_key)
        path = pathlib.Path(root_dir, sub_path)
        return path

    def get_dir(self, root_key, sub_key):
        return self._get_path(root_key, sub_key)

    def get_files(self, root_key, sub_key, suffixes=None):
        files = self._files[root_key][sub_key]
        if suffixes:
            return {key: value for key, value in files.items() if value.suffix in suffixes}
        return files

    def get_file_names(self, root_key, sub_key, suffixes=None):
        try:
            return sorted(self.get_files(root_key, sub_key, suffixes=suffixes))
        except KeyError:
            return None

    def create_dirs(self, root_key, *args):
        if not args:
            args = self.get_sub_keys(root_key)
        for sub_key in args:
            path = self._get_path(root_key, sub_key)
            path.mkdir(parents=True, exist_ok=True)

    def get_suffix_list(self, root_key, sub_key):
        self._check_sub_key(root_key, sub_key)
        return self._config[root_key][sub_key].get('suffixes', [])

    def _is_valid_suffix(self, root_key, sub_key, suffix):
        suffix_list = self.get_suffix_list(root_key, sub_key)
        if not suffix_list:
            return True
        if suffix.lower() in suffix_list:
            return True
        return False

    def store_files(self, root_key, *args):
        """Saves alla file paths in self._files. this is typically used to initiate content a directory"""
        if not args:
            args = self.get_sub_keys(root_key)
        for sub_key in args:
            self._store_files_in_dir(root_key, sub_key)

    def _get_sub_key_for_path(self, root_key, path):
        for sk in self.get_sub_keys(root_key):
            if self.get_dir(root_key, sk) == path:
                return sk

    def _store_files_in_dir(self, root_key, sub_key):
        self._check_sub_key(root_key, sub_key)
        self._files.setdefault(root_key, {})
        self._files[root_key].setdefault(sub_key, {})
        for path in self.get_dir(root_key, sub_key).iterdir():
            if path.is_dir():
                continue
            if not self._is_valid_suffix(root_key, sub_key, path.suffix):
                continue
            self._files[root_key][sub_key][path.name] = path

    def _add_file_to_dir(self, root_key, path):
        sub_key = self._get_sub_key_for_path(root_key, path.parent)
        if not sub_key:
            logger.debug(f'Will not add path not belonging to any sub_key: {path}')
            return
        self._check_sub_key(root_key, sub_key)
        self._files.setdefault(root_key, {})
        self._files[root_key].setdefault(sub_key, {})
        if path.is_dir():
            return
        if not self._is_valid_suffix(root_key, sub_key, path.suffix):
            logger.debug(f'Not a valid suffix to add for root_key {root_key} and sub_key {sub_key}: {path}')
            return
        self._files[root_key][sub_key][path.name] = path
        logger.debug(f'Added file with root_key={root_key} and sub_key={sub_key}: {path}')
        return True

    def _delete_file_from_dir(self, root_key, path):
        sub_key = self._get_sub_key_for_path(root_key, path.parent)
        if not sub_key:
            logger.debug(f'Will not delete path not belonging to any sub_key: {path}')
            return
        self._check_sub_key(root_key, sub_key)
        self._files.setdefault(root_key, {})
        self._files[root_key].setdefault(sub_key, {})
        p = self._files[root_key][sub_key].pop(path.name, None)
        if p:
            logger.debug(f'Deleted file with root_key={root_key} and sub_key={sub_key}: {path}')
            return True

    def _callback_monitor(self, data, *args, **kwargs):
        root_key = data.get('id')
        path = data.get('src_path')
        if path.is_dir():
            return
        event_type = data['event_type']
        if event_type == 'created':
            self._add_file_to_dir(root_key, path)
        elif event_type == 'deleted':
            self._delete_file_from_dir(root_key, path)
        for func in self._monitor_callbacks:
            func(data)

    def add_monitor_callback(self, func):
        if func in self._monitor_callbacks:
            logger.debug(f'Function already added as a monitor callback: {func}')
            return
        self._monitor_callbacks.append(func)

    def monitor_root_dir(self, root_key):
        self._check_root_dir(root_key)
        if root_key in self._watchers:
            logger.info(f'Watcher already activated for root_key: {root_key}')
            return
        self._watchers[root_key] = watcher.keep_watch_of_folder(folder=self.get_root_dir(root_key),
                                                                id=root_key,
                                                                func=self._callback_monitor)

    #
    # fh.set_root_dir('temp', r'C:\mw\temmp\temp_file_handler\local')
    # fh.set_root_dir('local', r'C:\mw\temmp\temp_file_handler\local')
    # fh.set_root_dir('server', r'C:\mw\temmp\temp_file_handler\server')
    # fh.create_dirs('temp')
    # fh.create_dirs('local')
    # fh.create_dirs('server')
    #
    # fh.monitor_root_dir('local')
