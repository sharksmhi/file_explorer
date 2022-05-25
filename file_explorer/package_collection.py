import pathlib

from file_explorer import utils
from file_explorer.package import Package


class PackageCollection:

    def __init__(self, name, packages=None):
        self._name = name
        self._packages = []

        if packages:
            self.add_packages(packages)

    def __call__(self, *args, **kwargs):
        if kwargs:
            packages = self.get_packages_matching(**kwargs)
        else:
            packages = self.packages
        attr_list = []
        for pack in packages:
            values = []
            for key in args:
                values.append(pack(key))
            if len(values) == 1:
                values = values[0]
            else:
                values = tuple(values)
            attr_list.append(values)
        return attr_list

    def __getitem__(self, key):
        for pack in self.packages:
            if pack.key == key:
                return pack

    def add_package(self, package):
        if not isinstance(package, Package):
            raise Exception('This is not a package')
        self._packages.append(package)

    def add_packages(self, package_list):
        for package in package_list:
            self.add_package(package)

    @property
    def name(self):
        return self._name

    @property
    def packages(self):
        return self._packages

    @property
    def keys(self):
        return [pack.key for pack in self.packages]

    def missing(self, key):
        mis = []
        for pack in self.packages:
            if not pack(key):
                item = pack.key or pack.files[0].name
                mis.append(item)
        return mis

    @property
    def nr_packages(self):
        return len(self.packages)

    @property
    def nr_files(self):
        return [(pack.key, len(pack.files)) for pack in self.packages]

    def get_packages_matching(self, as_collection=False, **kwargs):
        matching_packages = []
        for pack in self.packages:
            if utils.is_matching(pack, **kwargs):
                matching_packages.append(pack)
        if as_collection:
            return PackageCollection(f'subselection_{self.name}', matching_packages)
        return matching_packages

    def get_attributes_from_all_packages(self):
        all_list = []
        for pack in self.packages:
            all_list.append(pack.attributes.copy())
        return all_list

    def write_attributes_from_all_packages(self, directory):
        all_list = self.get_attributes_from_all_packages()
        header = set()
        for item in all_list:
            header.update(list(item.keys()))
        header = sorted(header)
        lines = []
        lines.append('\t'.join(header))
        for item in all_list:
            line = []
            for col in header:
                value = str(item.get(col))
                line.append(value)
            lines.append('\t'.join(line))

        path = pathlib.Path(directory, f'attributes_{self.name}.txt')
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as fid:
            fid.write('\n'.join(lines))

    def get_data(self, zpar=None, par=None, IN_zpar=None, IN_par=None, **kwargs):
        import pandas as pd
        all_data = {}
        tot_df = None
        unique_zpar = set()
        unique_par = set()
        for pack in self.get_packages_matching(**kwargs):
            data = pack.get_data(**kwargs)
            if data is None:
                continue
            if (zpar or IN_zpar) and (par or IN_par):
                if IN_zpar:
                    for col in data.columns:
                        if IN_zpar.lower() in col.lower():
                            zpar = col
                            break
                if IN_par:
                    for col in data.columns:
                        if IN_par.lower() in col.lower():
                            par = col
                            break
                if zpar not in data.columns or par not in data.columns:
                    continue
                unique_zpar.add(zpar)
                unique_par.add(par)

                df = pd.DataFrame()
                df[zpar] = data[zpar]
                if 'station' in kwargs:
                    col_name = str(pack('datetime'))
                else:
                    col_name = f"{pack('datetime')} - {pack('station')}"
                df[col_name] = data[par]

                df.set_index(zpar, inplace=True)
                if tot_df is None:
                    tot_df = df.copy(deep=True)
                else:
                    tot_df = tot_df.join(df, on=zpar)
            else:
                all_data[f"{pack('datetime')} - {pack('station')}"] = data

        if tot_df is None:
            raise Exception(f'No match for given parameters: zpar={zpar}, par={par}, IN_zpar={IN_zpar}, IN_par={IN_par}')

        if len(unique_zpar) != 1:
            print('Found several zpars:')
            print(unique_zpar)
        if len(unique_par) != 1:
            print('Found several pars:')
            print(unique_par)

        return all_data or tot_df.sort_index()

    def plot_data(self, zpar=None, par=None, IN_zpar=None, IN_par=None, **kwargs):
        import matplotlib.pyplot as plt

        df = self.get_data(zpar=zpar, par=par, IN_zpar=IN_zpar, IN_par=IN_par, **kwargs)
        with plt.style.context('ggplot'):
            for col in df.columns:
                plt.plot(df[col], -df.index, label=col)
            plt.legend(loc=3)
            if 'station' in kwargs:
                plt.title(f'Station name: {kwargs.get("station")}')
            elif 'IN_station' in kwargs:
                plt.title(f'"{kwargs.get("""IN_station""")}" in station name')
            plt.xlabel(par or f'"{IN_par}"', fontsize=12)
            plt.ylabel(zpar or f'"{IN_zpar}"', fontsize=12)
            plt.show()

    def write_data_to_directory(self, directory, **kwargs):
        import pathlib
        data = self.get_data(**kwargs)

        string_list = [self._name]
        for key, value in kwargs.items():
            string_list.append(f'{key}={value}')
        string = '_'.join(string_list)

        if isinstance(data, dict):
            for key, value in data.items():
                path = pathlib.Path(directory, string, f"{key.replace(':', '').replace('/', ' ')}.txt")
                path.parent.mkdir(parents=True, exist_ok=True)
                value.to_csv(path, sep='\t', index=False)
        else:
            path = pathlib.Path(directory, f"{string}.txt")
            data.to_csv(path, sep='\t')

    def get_latest_serno(self, **kwargs):
        """
        Returns the highest serno found in files. Check for matching criteria in kwargs first.
        :param serno:
        :return:
        """
        serno_list = [pack('serno') for pack in self.get_packages_matching(**kwargs)]
        if serno_list:
            return sorted(serno_list)[-1]

    def get_latest_series(self, path=False, **kwargs):
        serno = self.get_latest_serno(**kwargs)
        kwargs['serno'] = serno
        matching_packages = self.get_packages_matching(**kwargs)
        if not matching_packages:
            return None
        if len(matching_packages) > 1:
            raise ValueError('More than one matching file')
        obj = matching_packages[0]
        if path:
            return obj.path
        return obj

    def get_next_serno(self, **kwargs):
        latest_serno = self.get_latest_serno(**kwargs)
        if not latest_serno:
            return '0001'
        next_serno = str(int(latest_serno)+1).zfill(4)
        return next_serno

    def series_exists(self, **kwargs):
        matching = self.get_packages_matching(**kwargs)
        if not matching:
            return False
        return matching
