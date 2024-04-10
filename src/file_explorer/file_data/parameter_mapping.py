import yaml
from pathlib import Path
import re

MAPPING_FILE_PATH = Path(Path(__file__).parent, 'parameter_mapping.yaml')


def strip_par(par: str) -> str:
    return ''.join(re.findall('[a-z0-9]', par.lower()))
    # return par.lower().replace(' ', '')


def get_mapping_data_from_file() -> dict:
    with open(MAPPING_FILE_PATH) as fid:
        data = yaml.safe_load(fid)
    mapped = {}
    for key, values in data.items():
        for value in values:
            mapped[strip_par(value)] = key
    return mapped


class ParameterMapping:
    data = get_mapping_data_from_file()

    def __call__(self, par: str) -> str:
        return self.data.get(strip_par(par), par)

    def get_mapped_list(self, input_list: list) -> list:
        return [self(item) for item in input_list]


if __name__ == '__main__':
    d = get_mapping_data_from_file()
