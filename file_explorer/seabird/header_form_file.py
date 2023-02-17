from pathlib import Path
import logging

from file_explorer.seabird.hdr_file import HdrFile
from file_explorer.seabird.hex_file import HexFile

from file_explorer.seabird import utils


logger = logging.getLogger(__name__)

HEADER_FIELDS = (
    'Station',
    'Operator',
    'Ship',
    # 'Average sound velocity',
    # 'True-depth calculation',
    'Cruise',
    'Latitude [GG MM.mm N]',
    'Longitude [GGG MM.mm E]',
    'Pumps',
    'EventIDs',
    'Additional Sampling',
    'Metadata admin',
    'Metadata conditions',
    'LIMS Job',
)


PUMPS_LIST = [
    'PrimaryPump',
    'SecondaryPump'
]


EVENT_IDS_LIST = [
    'EventID',
    'ParentEventID'
]


METADATA_ADMIN_LIST = (
    'MPROG',
    'PROJ',
    'ORDERER',
    'SLABO',
    'ALABO',
    'REFSK'
)


METADATA_CONDITIONS_LIST = (
    'WADEP_BOT',
    'WADEP',
    'WINSP',
    'WINDIR',
    'AIRPRES',
    'AIRTEMP',
    'WEATH',
    'CLOUD',
    'WAVES',
    'ICEOB',
    'COMNT_VISIT'
)


class HeaderFormFile:

    def __init__(self, file):
        self._cls = None
        if isinstance(file, HdrFile):
            self._cls = HdrFile
        elif isinstance(file, HexFile):
            self._cls = HexFile
        else:
            msg = f'{file} is not a valid {self.__class__.__name__}'
            logger.error(msg)
            raise FileNotFoundError(msg)
        self._file = file

        self._old_header = []
        self._old_header_mapping = {}

        self._pre_lines = []
        self._header_lines = []
        self._post_lines = []

        self._metadata_admin_index = None
        self._metadata_condition_index = None

        self._header_fields_added = False

        self._read_lines()
        self._add_header_fields()

    def __getitem__(self, item):
        item = item.upper()
        for line in self._header_lines:
            if item not in line.upper():
                continue
            for key, value in utils.get_dict_from_header_form_line(line).items():
                if key.upper() == item:
                    return value

    def __setitem__(self, key, value):
        if value in [None, False]:
            value = ''
        else:
            value = str(value)
        self._add_header_fields()
        key = key.upper()

        if key in METADATA_ADMIN_LIST:
            line = self._header_lines[self._metadata_admin_index]
            par, item_str = line.split(':', 1)
            items = utils.metadata_string_to_dict(item_str)
            items[key] = value
            self._header_lines[self._metadata_admin_index] = f'** Metadata admin: ' \
                                                             f'{utils.metadata_dict_to_string(items)}'
            logger.debug(f'{key} is set to {value}')
            return

        if key in METADATA_CONDITIONS_LIST:
            line = self._header_lines[self._metadata_condition_index]
            par, item_str = line.split(':', 1)
            items = utils.metadata_string_to_dict(item_str)
            items[key] = value
            self._header_lines[self._metadata_condition_index] = f'** Metadata conditions: ' \
                                                                 f'{utils.metadata_dict_to_string(items)}'
            logger.debug(f'{key} is set to {value}')
            return

        for i, line in enumerate(self._header_lines):
            if key not in line.upper():
                continue

            par, info_str = [item.strip() for item in line.split(':', 1)]
            par = par.strip(' *')
            if par.upper() == key:
                new_line = f'** {par}: {value}'
                self._header_lines[i] = new_line
                logger.debug(f'{key} is set to {value}')
                return
        raise AttributeError(f'No such key to set: {key}')

    def __str__(self):
        sep_length = 130
        lines = []
        lines.append('-'*sep_length)
        lines.append(f'Header information in file: {self.path}')
        lines.append('-'*sep_length)
        lines.extend([item.strip() for item in self.header_lines])
        lines.append('-'*sep_length)
        return '\n'.join(lines)

    @property
    def path(self):
        return self._file.path

    @property
    def pre_lines(self):
        return self._pre_lines

    @property
    def header_lines(self):
        return self._header_lines

    @property
    def post_lines(self):
        return self._post_lines

    @property
    def all_lines(self):
        all_lines = []
        all_lines.extend(self.pre_lines)
        all_lines.extend(self.header_lines)
        all_lines.extend(self.post_lines)
        return all_lines

    def _read_lines(self):
        self._old_header = []
        self._old_header_mapping = {}
        self._pre_lines = []
        self._header_lines = []
        self._post_lines = []
        with open(self.path) as fid:
            for line in fid:
                line = line.strip()
                if line.startswith('**'):
                    self._old_header.append(line)
                    self._old_header_mapping[line.split(':', 1)[0].strip(' *')] = line
                    if 'metadata admin' in line.lower():
                        self._metadata_admin_index = len(self._old_header) - 1
                    elif 'metadata conditions' in line.lower():
                        self._metadata_condition_index = len(self._old_header) - 1
                elif self._old_header:
                    self._post_lines.append(line)
                else:
                    self._pre_lines.append(line)

        self._header_lines = self._old_header[:]

    def _add_header_fields(self):
        """
        Adds all default header fields (rows).
        """
        if self._header_fields_added:
            return
        old_header = self._old_header[:]
        new_header = []
        for field in HEADER_FIELDS:
            present_value = self._old_header_mapping.get(field)
            if present_value:
                new_header.append(self._get_enriched_header_field(present_value))
                old_header.pop(old_header.index(present_value))
            else:
                value = f'** {field}: '
                new_header.append(self._get_enriched_header_field(value))

        new_header.extend(old_header)
        self._header_lines = new_header

        self._metadata_admin_index = HEADER_FIELDS.index('Metadata admin')
        self._metadata_condition_index = HEADER_FIELDS.index('Metadata conditions')
        self._header_fields_added = True

    @staticmethod
    def _get_enriched_header_field(current_line):
        """ Enrich the given header field with default data. Also cleans the data from unwanted spaces. """
        key, value = current_line.split(':', 1)
        lower_key = key.lower()
        if 'pumps' in lower_key:
            default_dict = dict((k, '') for k in PUMPS_LIST)
        elif 'event' in lower_key:
            default_dict = dict((k, '') for k in EVENT_IDS_LIST)
        elif 'admin' in lower_key:
            default_dict = dict((k, '') for k in METADATA_ADMIN_LIST)
        elif 'conditions' in lower_key:
            default_dict = dict((k, '') for k in METADATA_CONDITIONS_LIST)
        else:
            return f'{key.strip()}: {value.strip()}'
        if '#' in value:
            value_dict = utils.metadata_string_to_dict(value)
            default_dict.update(value_dict)
        return f'{key}: {utils.metadata_dict_to_string(default_dict)}'

    def save_file(self, directory, overwrite=False):
        output_path = Path(directory, self.path.name)
        if output_path.exists() and not overwrite:
            raise FileExistsError(output_path)

        with open(output_path, 'w') as fid:
            fid.write('\n'.join(self.all_lines))

        return self._cls(output_path)
