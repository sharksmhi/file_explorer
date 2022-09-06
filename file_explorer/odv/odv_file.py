import datetime

from file_explorer.file import InstrumentFile
from file_explorer import file_data


class OdvFile(InstrumentFile):
    suffix = '.txt'

    def _save_info_from_file(self):
        self._parameters = []
        self._sdn_reference = None
        self._metadata = {}
        par_index = 0
        header = []
        metadata_max_index = None
        with open(self.path, encoding='utf8') as fid:
            for r, line in enumerate(fid):
                strip_line = line.strip()
                if not strip_line:
                    continue
                if 'xlink:href' in strip_line:
                    self._sdn_reference = strip_line.split('"')[1]
                elif strip_line.startswith('//') and 'P01' in strip_line:
                    split_line = strip_line.split(':')
                    short_name = split_line[2].split('<')[0]
                    p01 = split_line[5].split('<')[0]
                    p06 = split_line[8].split('<')[0]
                    self._parameters.append(dict(short_name=short_name, p01=p01, p06=p06, index=par_index))
                    par_index += 1
                elif strip_line.startswith('//'):
                    continue
                elif strip_line.startswith('Cruise'):
                    header = strip_line.split('\t')
                    metadata_max_index = len(header) - len(self._parameters)*2
                    for par, item in zip(self._parameters, header[metadata_max_index::2]):
                        par['name'] = item
                elif not line.startswith('\t'):
                    metadata = strip_line.split('\t')[:metadata_max_index]
                    self._metadata = dict(zip(header[:metadata_max_index], metadata))

    def _save_attributes(self):
        self._attributes['parameters'] = self._parameters
        self._attributes['sdn_reference'] = self._sdn_reference
        for key, value in self._metadata.items():
            self._attributes[key.lower()] = value
        self._attributes['lat'] = self._metadata['Latitude [degrees_north]'].lstrip('+')
        self._attributes['lon'] = self._metadata['Longitude [degrees_east]'].lstrip('+0')

    def _get_datetime(self):
        value = self._metadata['yyyy-mm-ddThh:mm:ss.sss']
        if len(value) == 23:
            return datetime.datetime.strptime(value, '%Y-%m-%dt%H:%M:%S.%f')
        else:
            return datetime.datetime.strptime(value, '%Y-%m-%dt%H:%M:%S')

    @property
    def data(self):
        if self._data is None:
            self._data = get_data_object(self.path, metadata=self._metadata)
        return self._data


def get_data_object(path, metadata=None):
    import pandas as pd
    from io import StringIO
    nr_metadata = len(metadata)
    with open(path) as fid:
        lines = [line.rstrip() for line in fid if line.strip() and '//' not in line]
    full_header = []
    data_list = []
    metadata = []
    for r, line in enumerate(lines):
        split_line = line.split('\t')
        if line.startswith('Cruise'):
            full_header = split_line
            header = [item for item in split_line if item != 'QV:SEADATANET']
            data_list.append('\t'.join(header))
            metadata = lines[r+1].split('\t')[:nr_metadata]
        else:
            data = []
            for fullh, lined in zip(full_header[nr_metadata:], split_line[nr_metadata:]):
                if fullh == 'QV:SEADATANET':
                    continue
                data.append(lined)
            data_list.append('\t'.join(metadata + data))
    df = pd.read_csv(StringIO('\n'.join(data_list)), sep='\t', encoding='cp1252')
    return file_data.Data(df)
