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
            if pack.is_matching(**kwargs):
                matching_packages.append(pack)
        if as_collection:
            return PackageCollection(f'subselection_{self.name}', matching_packages)
        return matching_packages

    def get_data(self, zpar=None, par=None, in_par=None, **kwargs):
        import pandas as pd
        all_data = []
        tot_df = None
        for pack in self.packages:
            if not pack.is_matching(**kwargs):
                continue
            data = pack.get_data(**kwargs)
            if data is None:
                continue
            if zpar and (par or in_par):
                if in_par:
                    for col in data.columns:
                        if in_par.lower() in col.lower():
                            par = col
                            break
                if zpar not in data.columns or par not in data.columns:
                    continue
                df = pd.DataFrame()
                df[zpar] = data[zpar]
                if 'station' in kwargs:
                    col_name = str(pack('datetime'))
                else:
                    col_name = f"{pack('station')} - {pack('datetime')}"
                df[col_name] = data[par]
                df.set_index(zpar, inplace=True)
                if tot_df is None:
                    tot_df = df.copy(deep=True)
                else:
                    tot_df = tot_df.join(df, on=zpar)
            else:
                all_data.append(data)

        return all_data or tot_df

    def plot_data(self, zpar=None, par=None, **kwargs):
        import matplotlib.pyplot as plt

        df = self.get_data(zpar, par, **kwargs)
        with plt.style.context('ggplot'):
            for col in df.columns:
                plt.plot(df[col], -df.index, label=col)
            plt.legend(loc=3)
            if 'station' in kwargs:
                plt.title(kwargs.get('station'))
            plt.xlabel(par, fontsize=12)
            plt.ylabel(zpar, fontsize=12)
            plt.show()


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
