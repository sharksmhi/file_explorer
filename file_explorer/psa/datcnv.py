from .psa_file import PSAfile
from pathlib import Path
from file_explorer.seabird import compare
import shutil
import datetime


class DatCnvPSAfile(PSAfile):

    def __init__(self, file_path):
        super().__init__(file_path)

    def get_parameter_info(self):
        pars = self.tree.find('CalcArray').getchildren()
        pars_info = []
        for par in pars:
            info = {}
            info.update(par.attrib)
            calc = par.find('Calc')
            info.update(calc.attrib)
            full_name = calc.find('FullName')
            info.update(full_name.attrib)
            info['name'] = info['value']
            pars_info.append(info)
        return pars_info


class ManipulateDatCnv:
    def __init__(self, path):
        self._path = Path(path)
        self._lines = []

    def remove_parameters_not_in_xmlcon(self, xmlcon):
        comp = compare.get_datcnv_and_xmlcon_pars_mismatch(datcnv=self._path, xmlcon=xmlcon)
        not_in_xmlcon = comp.get('not_in_xmlcon')
        if not not_in_xmlcon:
            return
        self._save_lines_in_file()
        for par in not_in_xmlcon:
            self._remove_par(par)

    def _save_lines_in_file(self):
        with open(self._path) as fid:
            self._lines = fid.readlines()

    def _remove_par(self, par):
        self._remove_par_block(par)
        self._change_index()
        self._save_file()

    def _remove_par_block(self, par):
        new_lines = []
        include = True
        for r, line in enumerate(self._lines):
            if 'index' in line:
                include = True
                if par in self._lines[r+2]:
                    include = False
            if include:
                new_lines.append(line)
        self._lines = new_lines

    def _change_index(self):
        new_lines = []
        current_index = -1
        for line in self._lines:
            if '<CalcArray Size=' in line:
                split_line = line.split('"')
                i = int(split_line[1]) - 1
                new_split_line = split_line[:1] + [str(i)] + split_line[2:]
                line = '"'.join(new_split_line)
            elif 'index' in line:
                split_line = line.split('"')
                index = int(split_line[1])
                current_index += 1
                if index != current_index:
                    new_split_line = split_line[:1] + [str(current_index)] + split_line[2:]
                    line = '"'.join(new_split_line)
            new_lines.append(line)
        self._lines = new_lines

    def _save_file(self):
        self._copy_old_file()
        with open(self._path, 'w') as fid:
            fid.write(''.join(self._lines))

    def _copy_old_file(self):
        day_str = datetime.datetime.now().strftime('%Y%m%d')
        now_str = datetime.datetime.now().strftime('%Y%m%d_%H_%M_%S')
        target_dir = Path(self._path.parent, day_str)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = Path(target_dir, f'{now_str}_{self._path.name}')
        shutil.copy2(self._path, target_path)
