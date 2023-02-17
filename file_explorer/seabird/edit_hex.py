from file_explorer.seabird.header_form_file import HeaderFormFile
from file_explorer.seabird.hex_file import HexFile


def update_hex_file(file, output_directory, overwrite=False, **data):
    assert isinstance(file, HexFile)
    obj = HeaderFormFile(file)
    for key, value in data.items():
        obj[key] = value
    return obj.save_file(output_directory, overwrite=overwrite)
