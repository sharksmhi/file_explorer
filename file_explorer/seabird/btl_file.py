from pathlib import Path
import datetime

from file_explorer.file import InstrumentFile


class BtlFile(InstrumentFile):
    suffix = '.btl'

    def _save_info_from_file(self):
        pass