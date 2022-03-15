from file_explorer import mapping
from file_explorer.file import InstrumentFile
from file_explorer.seabird import xmlcon_parser


class XmlFile(InstrumentFile):
    suffix = '.xml'
    _tree = None
    _sensor_info = None

    def _save_info_from_file(self):
        self._tree = xmlcon_parser.get_parser_from_file(self.path)
        self._sensor_info = xmlcon_parser.get_sensor_info(self._tree)

    def _save_attributes(self):
        self._attributes['sensor_info'] = self._sensor_info
        self._attributes['instrument'] = self.instrument
        self._attributes['instrument_number'] = self.instrument_number

    @property
    def instrument_number(self):
        data = xmlcon_parser.get_hardware_data(self._tree)
        return data['SerialNumber']

    @property
    def instrument(self):
        data = xmlcon_parser.get_hardware_data(self._tree)
        return mapping.get_instrument_mapping(data['DeviceType'])

    @property
    def sensor_info(self):
        return self._sensor_info
