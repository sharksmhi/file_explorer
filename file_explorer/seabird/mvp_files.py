from file_explorer.file import InstrumentFile


class LogFile(InstrumentFile):
    suffix = '.log'

    def _save_info_from_file(self):
        self._file_info = {}
        with open(self.path) as fid:
            for line in fid:
                if 'END_OF_HEADER' in line:
                    break
                if ':' in line:
                    strip_line = line.strip()
                    key, value = strip_line.split(':', 1)
                    self._file_info[key.strip().lower()] = value.strip()

    def _save_attributes(self):
        self._attributes.update(self._file_info)


class EngFile(InstrumentFile):
    suffix = '.eng'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class M1File(InstrumentFile):
    suffix = '.m1'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class RawFile(InstrumentFile):
    suffix = '.raw'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class AscFile(InstrumentFile):
    suffix = '.asc'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class AsvpFile(InstrumentFile):
    suffix = '.asvp'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class CalcFile(InstrumentFile):
    suffix = '.calc'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class Em1File(InstrumentFile):
    suffix = '.em1'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class RnnFile(InstrumentFile):
    suffix = '.rnn'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class S10File(InstrumentFile):
    suffix = '.s10'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class S12File(InstrumentFile):
    suffix = '.s12'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class S52File(InstrumentFile):
    suffix = '.s52'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass


class CnvFile(InstrumentFile):
    suffix = '.cnv'

    def _save_info_from_file(self):
        pass

    def _save_attributes(self):
        pass
