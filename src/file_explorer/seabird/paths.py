from pathlib import Path
import datetime
import os
import shutil


class SBEPaths:
    """Will be replaced by file_explorer.file_handler.FileHandler in the future. Still used by some applications. """
    def __init__(self):
        self._paths = {}
        self._year = None
        self._sub_dir_list_local = ['source', 'raw', 'cnv', 'data', 'cnv_up', 'plots', 'temp']
        self._sub_dir_list_server = ['raw', 'cnv', 'data', 'cnv_up', 'plots']

    def __call__(self, key, create=False, default=None, **kwargs):
        path = self._paths.get(key)
        if not path:
            if default is not None:
                return default
            return False
        if create and not path.exists():
            os.makedirs(str(path))
        return path

    def _clean_temp_folder(self):
        """ Deletes old files in the temp folder """
        if not self.get_local_directory('temp').exists():
            return
        now = datetime.datetime.now()
        dt = datetime.timedelta(days=2)
        for path in self.get_local_directory('temp').iterdir():
            # unix_time = os.path.getmtime(path)
            unix_time = os.path.getctime(path)
            t = datetime.datetime.fromtimestamp(unix_time)
            if t < now-dt:
                try:
                    if path.is_file():
                        os.remove(path)
                    else:
                        shutil.rmtree(path)
                except PermissionError:
                    pass

    @property
    def year(self):
        return self._year

    @property
    def local_sub_directories(self):
        return self._sub_dir_list_local

    @property
    def server_sub_directories(self):
        return self._sub_dir_list_server

    def _local_key(self, key=None):
        if key not in self.local_sub_directories + ['root']:
            raise Exception(f'Not a valid sub directory: {key}')
        return f'local_dir_{key}'

    def _server_key(self, key=None):
        if key not in self.server_sub_directories + ['root']:
            raise Exception(f'Not a valid sub directory: {key}')
        return f'server_dir_{key}'

    def get_path(self, key):
        return self._paths.get(key, None)

    def get_local_directory(self, key, year=None, create=False, default=None):
        if key == 'source':
            return self._paths.get('local_dir_source')
        elif key == 'temp':
            return self._paths.get('local_dir_temp')
        elif key == 'root':
            return self._paths.get('local_dir_root')
        year = year or self.year
        if year:
            return self._get_local_directory_for_year(key, year, create=create)
        return self(self._local_key(key), create=create, default=default)

    def get_server_directory(self, key, year=None, create=False, default=None):
        # year = year or self.year
        if year:
            return self._get_server_directory_for_year(key, year, create=create)
        return self(self._server_key(key), create=create, default=default)

    def create_local_paths(self):
        for key in self._sub_dir_list_local:
            self.get_local_directory(key, create=True)

    def create_server_paths(self, year=None):
        for key in self._sub_dir_list_server:
            self.get_server_directory(key, year=year, create=True)

    def _get_local_directory_for_year(self, key, year, create=False):
        if key not in self._sub_dir_list_local:
            raise Exception(f'Invalid directory: {key}')
        path = Path(self._paths['local_dir_root'], str(year), key)
        if create and not path.exists():
            os.makedirs(path)
        return path

    def _get_server_directory_for_year(self, key, year, create=False):
        if not self._paths.get('server_dir_root'):
            return
        if key not in self._sub_dir_list_server:
            raise Exception(f'Invalid directory: {key}')
        path = Path(self._paths['server_dir_root'], str(year), key)
        if create and not path.exists():
            os.makedirs(path)
        return path

    def set_config_root_directory(self, path):
        self._paths['config_dir'] = Path(path).absolute()
        self._paths['instrumentinfo_file'] = Path(self._paths['config_dir'], 'Instruments.xlsx')

    def set_source_directory(self, path):
        path = Path(path).absolute()
        if not path.is_dir():
            raise NotADirectoryError(path)
        self._paths['local_dir_source'] = Path(path)

    def set_local_root_directory(self, directory):
        root_directory = Path(directory).absolute()
        if root_directory.name in ['temp', 'source', 'raw', 'cnv', 'data', 'plots']:
            root_directory = root_directory.parent.parent
        self._paths['local_dir_root'] = root_directory
        self.set_year()
        self._clean_temp_folder()

    def set_server_root_directory(self, directory):
        root_directory = Path(directory).absolute()
        if root_directory.name in ['raw', 'cnv', 'data']:
            root_directory = root_directory.parent
        self._paths['server_dir_root'] = root_directory
        self.set_year()

    def set_year(self, year=None):
        """ Year is needed to set sub directories for the different filetypes """
        self._year = str(year or self._year or datetime.datetime.now().year)
        if self._paths.get('server_dir_root'):
            self._paths['server_dir_raw'] = Path(self._paths['server_dir_root'], self._year, 'raw')
            self._paths['server_dir_cnv'] = Path(self._paths['server_dir_root'], self._year, 'cnv')
            self._paths['server_dir_data'] = Path(self._paths['server_dir_root'], self._year, 'data')
            self._paths['server_dir_cnv_up'] = Path(self._paths['server_dir_root'], self._year, 'cnv', 'up_cast')
            self._paths['server_dir_plot'] = Path(self._paths['server_dir_root'], self._year, 'plots')
        if self._paths.get('local_dir_root'):
            self._paths['working_dir'] = Path(self._paths['local_dir_root'], 'temp')
            self._paths['local_dir_temp'] = self._paths['working_dir']
            # self._paths['local_dir_source'] = Path(self._paths['local_dir_root'], self._year, 'source')
            self._paths['local_dir_raw'] = Path(self._paths['local_dir_root'], self._year, 'raw')
            self._paths['local_dir_cnv'] = Path(self._paths['local_dir_root'], self._year, 'cnv')
            self._paths['local_dir_cnv_up'] = Path(self._paths['local_dir_root'], self._year, 'cnv', 'up_cast')
            self._paths['local_dir_data'] = Path(self._paths['local_dir_root'], self._year, 'data')
            self._paths['local_dir_plot'] = Path(self._paths['local_dir_root'], self._year, 'plots')
