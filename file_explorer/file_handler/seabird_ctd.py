
from pathlib import Path
import shutil
import filecmp
import pathlib
import datetime
import os

from ctd_processing import exceptions

import file_explorer
from file_explorer.file_handler import FileHandler
from file_explorer import get_file_object_for_path

import logging


logger = logging.getLogger(__name__)

PREFIX_SUFFIX_SUBFOLDER_MAPPING = {
    (None, '.cnv'): 'cnv',
    (None, '.sensorinfo'): 'cnv',
    (None, '.metadata'): 'cnv',
    (None, '.deliverynote'): 'cnv',
    ('u', '.cnv'): 'cnv_up',
    (None, '.jpg'): 'plot',
    (None, '.bl'): 'raw',
    (None, '.btl'): 'raw',
    (None, '.hdr'): 'raw',
    (None, '.hex'): 'raw',
    (None, '.ros'): 'raw',
    (None, '.xmlcon'): 'raw',
    (None, '.con'): 'raw',
    (None, '.zip'): 'raw',
    (None, '.txt'): 'nsf',
}
#
#
# SUBDIR_SUFFIX_MAPPING = {
#     'source': '.hex',
#     'cnv': '.cnv',
#     'nsf': '.txt'
# }
#
#
# def file_is_mapped_to_subdir(path, subdir):
#     suffix = SUBDIR_SUFFIX_MAPPING.get(subdir)
#     if not suffix:
#         return True
#     if suffix == path.suffix:
#         return True
#     return False


class SBEFileHandler(FileHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.paths = paths_object
        self._all_files_by_stem = {}
        self._all_files_by_cruise = {}
        # self._all_local_files_by_directory = {}
        # self._all_server_files_by_directory = {}
        # self.local_files = {}
        # self.server_files = {}

        # self.count = 0

    @property
    def local_sub_directories(self):
        return self.get_sub_keys('local')

    @property
    def server_sub_directories(self):
        return self.get_sub_keys('server')

    @property
    def instrument_file_path(self):
        return pathlib.Path(self.get_dir('config', 'root'), 'Instruments.xlsx')

    def inspect_all_files_in_root_dir(self, root_key):
        self.create_dirs(root_key)
        self.store_files(root_key)

    def _reset_files(self, root_key):
        super()._reset_files(root_key)
        self._all_files_by_stem[root_key] = {}
        self._all_files_by_cruise[root_key] = {}

    def _store_files_in_dir(self, root_key, sub_key):
        self._check_sub_key(root_key, sub_key)
        self._files.setdefault(root_key, {})
        self._files[root_key].setdefault(sub_key, {})
        self._all_files_by_stem.setdefault(root_key, {})
        self._all_files_by_cruise.setdefault(root_key, {})
        for path in self.get_dir(root_key, sub_key).iterdir():
            if path.is_dir():
                continue
            if not self._is_valid_suffix(root_key, sub_key, path.suffix):
                continue
            self._files[root_key][sub_key][path.name] = path
            # obj = File(path)
            obj = get_file_object_for_path(path, instrument_type='sbe', load_file=False)  # This will not
            # load information from withing the file.
            if not obj:
                continue
            self._all_files_by_stem[root_key].setdefault(obj.pattern, {})
            self._all_files_by_stem[root_key][obj.pattern][(sub_key, obj.name)] = obj
            self._all_files_by_cruise[root_key].setdefault(obj.cruise, {})
            self._all_files_by_cruise[root_key][obj.cruise][(sub_key, obj.name)] = obj

    def get_all_files_by_cruise(self, root_key, cruise):
        self._check_root_key(root_key)
        return self._all_files_by_cruise[root_key][cruise]

    def _add_file_to_dir(self, root_key, path):
        if not super()._add_file_to_dir(root_key, path):
            return
        sub_key = self._get_sub_key_for_path(root_key, path.parent)
        # obj = File(path)
        obj = get_file_object_for_path(path, instrument_type='sbe', load_file=False)
        if not obj:
            return
        self._all_files_by_stem[root_key].setdefault(obj.pattern, {})
        self._all_files_by_stem[root_key][obj.pattern][(sub_key, obj.name)] = obj
        self._all_files_by_cruise[root_key].setdefault(obj.cruise, {})
        self._all_files_by_cruise[root_key][obj.cruise][(sub_key, obj.name)] = obj

    def _delete_file_from_dir(self, root_key, path):
        if not super()._delete_file_from_dir(root_key, path):
            return
        sub_key = self._get_sub_key_for_path(root_key, path.parent)
        # obj = File(path)
        obj = get_file_object_for_path(path, instrument_type='sbe', load_file=False)
        if not obj:
            return
        # print(f'{root_key=}')
        # print(f'{self._all_files_by_stem[root_key]=}')
        self._all_files_by_stem[root_key][obj.pattern].pop((sub_key, obj.name), None)
        self._all_files_by_cruise[root_key][obj.cruise].pop(sub_key, obj.name, None)

    def _clean_temp_folder(self):
        """ Deletes old files in the temp folder """
        if not self.get_dir('temp').exists():
            return
        now = datetime.datetime.now()
        dt = datetime.timedelta(days=2)
        for path in self.get_dir('temp').iterdir():
            # unix_time = os.path.getmtime(path)
            unix_time = os.path.getctime(path)
            t = datetime.datetime.fromtimestamp(unix_time)
            if t < now - dt:
                try:
                    if path.is_file():
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                except PermissionError:
                    pass

    def select_file(self, path):
        """ This will load all files matching the file_paths file stem. Loading files in paths_object. """
        file_stem = Path(path).stem
        self.select_stem(file_stem)

    def select_stem(self, stem):
        if not stem.startswith('SBE'):
            raise exceptions.InvalidFileNameFormat('Not a valid file')
        year = stem.split('_')[2][:4]
        self.set_year(year)
        self._load_files(stem)

    def select_pack(self, pack):
        self.set_year(pack('year'))
        self._load_files(pack.pattern)

    # def clear_all_files(self):
    #     self._all_local_files_by_stem = {}
    #     self._all_server_files_by_stem = {}
    #
    # def update_all_files(self):
    #     self.update_all_local_files()
    #     self.update_all_server_files()
    #
    # def update_all_local_files(self, subdir=None):
    #     self.count += 1
    #     print(f'{self.count=}')
    #     self._all_local_files_by_directory = {}
    #     # self._all_local_files_by_stem = {}
    #     # self._all_local_files_by_directory = {}
    #     # for sub in self.paths.local_sub_directories:
    #     for sub in ['source', 'raw', 'cnv', 'nsf']:
    #         if subdir and sub != subdir:
    #             continue
    #         local_path = self.paths.get_local_directory(sub, create=True)
    #         print(f'{sub=}: {local_path=}')
    #         if not local_path:
    #             continue
    #         for path in local_path.iterdir():
    #             if path.is_dir():
    #                 continue
    #             if not file_is_mapped_to_subdir(path=path, subdir=sub):
    #                 continue
    #             obj = File(path)
    #             self._all_local_files_by_stem.setdefault(obj.stripped_stem, {})
    #             self._all_local_files_by_stem[obj.stripped_stem][(sub, obj.name)] = obj
    #             directory = str(obj.directory)
    #             self._all_local_files_by_directory.setdefault(directory, [])
    #             self._all_local_files_by_directory[directory].append(obj.name)
    #
    # def update_all_server_files(self, subdir=None):
    #     # for sub in self.paths.server_sub_directories:
    #     for sub in ['raw', 'cnv', 'nsf']:
    #         if subdir and sub != subdir:
    #             continue
    #         server_path = self.paths.get_server_directory(sub, create=True)
    #         if not server_path:
    #             continue
    #         for path in server_path.iterdir():
    #             if path.is_dir():
    #                 continue
    #             if not file_is_mapped_to_subdir(path=path, subdir=sub):
    #                 continue
    #             obj = File(path)
    #             self._all_server_files_by_stem.setdefault(obj.stripped_stem, {})
    #             self._all_server_files_by_stem[obj.stripped_stem][(sub, obj.name)] = obj
    #             directory = str(obj.directory)
    #             self._all_server_files_by_directory.setdefault(directory, [])
    #             self._all_server_files_by_directory[directory].append(obj.name)

    def _load_files(self, file_stem):
        self._load_local_files(file_stem)
        self._load_server_files(file_stem)

    def _load_local_files(self, file_stem):
        # self.local_files = self._all_local_files_by_stem.get(file_stem, {})
        self.local_files = self._all_files_by_stem['local'].get(file_stem, {})
        # self.local_files = {}
        # for sub in self.paths.local_sub_directories:
        #     local_path = self.paths.get_local_directory(sub, create=True)
        #     if local_path:
        #         for path in local_path.iterdir():
        #             if file_stem.lower() in path.stem.lower(): # this is to include upcast with prefix "u"
        #             # if file_stem == path.stem:
        #                 obj = File(path)
        #                 self.local_files[(sub, obj.name)] = obj

    def _load_server_files(self, file_stem):
        # self.server_files = self._all_server_files_by_stem.get(file_stem, {})
        self.server_files = self._all_files_by_stem['server'].get(file_stem, {})
        # self.server_files = {}
        # for sub in self.paths.server_sub_directories:
        #     server_path = self.paths.get_server_directory(sub, create=True)
        #     if server_path:
        #         for path in server_path.iterdir():
        #             if file_stem.lower() in path.stem.lower():  # this is to include upcast with prefix "u"
        #                 # if file_stem == path.stem:
        #                 obj = File(path)
        #                 self.server_files[(sub, obj.name)] = obj

    def get_file_path(self, root_key, sub_key, name):
        if root_key == 'local':
            return self.local_files[(sub_key, name)].path
        elif root_key == 'server':
            return self.server_files[(sub_key, name)].path

    def _not_on_server(self):
        """ Returns a dict with the local files that are not on server """
        result = {}
        sub_keys = self.get_sub_keys('server')
        for key, path in self.local_files.items():
            sub, name = key
            if sub not in sub_keys:
                continue
            if not self.server_files.get(key):
                result[key] = path
        return result

    def _not_updated_on_server(self):
        """ Returns a dict with local files that are not updated on server """
        result = {}
        for key, server in self.server_files.copy().items():
            local = self.local_files.get(key)
            if not local:
                continue
            if local == server:
                continue
            result[key] = local
        return result

    def not_on_server(self):
        return bool(self._not_on_server())

    def not_updated_on_server(self):
        return bool(self._not_updated_on_server())

    # def get_files_in_directory(self, directory):
    #     print(f'{self._all_local_files_by_directory.keys()=}')
    #     return self._all_local_files_by_directory.get(directory, [])

    def copy_files_to_server(self, update=False):
        for key, path_obj in self._not_on_server().items():
            sub, name = key
            server_directory = self.get_dir('server', sub)
            if not server_directory:
                continue
            target_path = Path(server_directory, path_obj.name)
            shutil.copy2(path_obj.path, target_path)
        if update:
            for key, path_obj in self._not_updated_on_server().items():
                sub, name = key
                server_directory = self.get_dir('server', sub)
                if not server_directory:
                    continue
                target_path = Path(server_directory, path_obj.name)
                shutil.copy2(path_obj.path, target_path)

    # def get_local_file_path(self, subdir=None, suffix=None):
    #     paths = []
    #     for key, file in self.local_files.items():
    #         if key[0] == subdir:
    #             if suffix and file.suffix == suffix:
    #                 return file.path
    #             paths.append(file.path)
    #     if len(paths) == 1:
    #         return paths[0]
    #     return paths


class File:
    def __init__(self, file_path):
        self.path = Path(file_path)

    def __str__(self):
        return str(self.path)

    def __call__(self):
        return self.path

    def __eq__(self, other):
        if not other:
            return None
        return filecmp.cmp(self.path, other(), shallow=False)

    @property
    def name(self):
        return self.path.name

    @property
    def directory(self):
        return self.path.parent

    @property
    def stripped_stem(self):
        return '_'.join(self.path.stem.lstrip('u').lstrip('d').split('_')[:7]).upper()

    @property
    def suffix(self):
        return self.path.suffix

    @property
    def cruise(self):
        try:
            return self.name.split('_')[-2]
        except IndexError:
            return None


def copy_package_to_local(pack, fhandler: FileHandler, overwrite=False, rename=False):
    """
    Copy all files in package to local. Returning new package.
    """
    fhandler.set_year(pack('year'))
    new_file_paths = []
    for file in pack.get_files():
        path = file.path
        key1 = (file.prefix, file.suffix)
        key2 = (None, file.suffix)
        key = PREFIX_SUFFIX_SUBFOLDER_MAPPING.get(key1) or PREFIX_SUFFIX_SUBFOLDER_MAPPING.get(key2)
        if not key:
            logger.info(f'Can not find destination subfolder for file: {path}')
            continue
        fhandler.create_dirs('local')
        target_dir = fhandler.get_dir('local', key)
        if rename:
            target_path = Path(target_dir, file.get_proper_name())
        else:
            target_path = Path(target_dir, path.name)
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        shutil.copy2(path, target_path)
        new_file_paths.append(target_path)

    packs = file_explorer.get_packages_from_file_list(new_file_paths, as_list=True)
    if len(packs) > 1:
        raise Exception(f'To many packages were created. Something went wrong!')
    return packs[0]


def copy_package_to_temp(pack, fhandler:FileHandler, overwrite=False, rename=False):
    fhandler.set_year(pack('year'))
    return file_explorer.copy_package_to_directory(pack,
                                                   fhandler.get_dir('local', 'temp'),
                                                   overwrite=overwrite,
                                                   rename=rename)


def get_seabird_config_path():
    return pathlib.Path(pathlib.Path(__file__).parent, 'config', 'seabird.yaml')


def get_seabird_file_handler(**kwargs):
    path = get_seabird_config_path()
    fh = SBEFileHandler.from_yaml(path)
    if kwargs.get('year'):
        fh.set_year(kwargs.get('year'))
    return fh
