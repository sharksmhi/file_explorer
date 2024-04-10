from pathlib import Path
import datetime

from file_explorer.file import InstrumentFile


class PrsFile(InstrumentFile):
    suffix = '.prs'
    _all_metadata = None

    @property
    def number_of_bottles(self):
        return self._number_of_bottles

    def _save_info_from_file(self):
        self._all_metadata = {}
        with open(self.path, encoding='ansi') as fid:
            for line in fid:
                if line.startswith('-'):
                    break
                if '|' not in line:
                    continue
                split_line = [item.strip() for item in line.strip().strip('|').split('|')]
                for part in split_line:
                    split_part = [item.strip(' .#') for item in part.split(':', 1)]
                    self._all_metadata[split_part[0]] = split_part[1].replace(' ', '')

    def _save_attributes(self):
        self._attributes['lat'] = self._all_metadata['St.Lat']
        self._attributes['lon'] = self._all_metadata['St.Long']
        self._attributes['date_str'] = self._all_metadata['Date']
        self._attributes['time_str'] = self._all_metadata['St.Time']
        self._attributes['ship'] = self._all_metadata['Vessel']
        self._attributes['cruise'] = self._all_metadata['Cruise']
        self._attributes['depth'] = self._all_metadata['Depth']

        split_operator = self._all_metadata['Operator'].split('/')
        if len(split_operator) == 2:
            self._attributes['station'] = split_operator[0]
            self._attributes['operator'] = split_operator[1]

    def _get_datetime(self):
        return datetime.datetime.strptime(f"{self._attributes['date_str']} {self._attributes['time_str']}", '%d-%b-%Y %H:%M:%S')

    @property
    def data(self):
        import pandas as pd
        from io import StringIO
        header = []
        passed_header = False
        with open(self.path, encoding='ansi') as fid:
            data = []
            for line in fid:
                if not line.strip():
                    continue
                if line.startswith('-'):
                    passed_header = True
                    continue
                if passed_header and line.strip().startswith('SCAN'):
                    header = [item.strip(' *') for item in line.split()]
                    data.append('\t'.join(header))
                    continue
                if header:
                    split_line = header = [item.strip(',') for item in line.split()]
                    data.append('\t'.join(split_line))
        df = pd.read_csv(StringIO('\n'.join(data)), sep='\t', encoding='cp1252')
        return df