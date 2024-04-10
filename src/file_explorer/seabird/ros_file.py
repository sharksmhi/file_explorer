from pathlib import Path
import datetime

from file_explorer.file import InstrumentFile


class RosFile(InstrumentFile):
    suffix = '.ros'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass
