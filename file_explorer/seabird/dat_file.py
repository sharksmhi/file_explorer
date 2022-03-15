
from file_explorer.file import InstrumentFile


class DatFile(InstrumentFile):
    suffix = '.dat'

    def _save_info_from_file(self):
        """ Binary file, sort of """
        pass

    def _save_attributes(self):
        pass
