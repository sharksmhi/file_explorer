import pathlib

import xml.etree.ElementTree as ET
from file_explorer.seabird import utils
from .psa_file_with_plot import PSAfileWithPlot


AUTO_FIRE_DATA_DATATYPE = list[dict[str, int | float]]

AUTO_FIRE_BOTTLE_KEYS = sorted(['index', 'BottleNumber', 'FireAt'])


class SeasavePSAfile(PSAfileWithPlot):
    def __init__(self, file_path):
        super().__init__(file_path)

        self.parameter_min_tag = 'MinimumValue'
        self.parameter_max_tag = 'MaximumValue'

        self.xmlcon_name_tags = ['Settings', 'ConfigurationFilePath']
        self.data_file_tags = ['Settings', 'DataFilePath']
        self.auto_fire_tags = ['Settings', 'WaterSamplerConfiguration']
        self.auto_fire_data_tags = ['Settings', 'WaterSamplerConfiguration', 'AutoFireData']
        self.auto_fire_bottle_tags = ['Settings', 'WaterSamplerConfiguration', 'AutoFireData', 'DataTable']

        self.station_tags = ['Settings', 'HeaderForm', 'Prompt{{index==0}}']
        self.operator_tags = ['Settings', 'HeaderForm', 'Prompt{{index==1}}']
        self.ship_tags = ['Settings', 'HeaderForm', 'Prompt{{index==2}}']
        self.cruise_tags = ['Settings', 'HeaderForm', 'Prompt{{index==3}}']
        self.lat_tags = ['Settings', 'HeaderForm', 'Prompt{{index==4}}']
        self.lon_tags = ['Settings', 'HeaderForm', 'Prompt{{index==5}}']
        self.pump_tags = ['Settings', 'HeaderForm', 'Prompt{{index==6}}']
        self.id_tags = ['Settings', 'HeaderForm', 'Prompt{{index==7}}']
        self.add_samp_tags = ['Settings', 'HeaderForm', 'Prompt{{index==8}}']
        self.metadata_admin_tags = ['Settings', 'HeaderForm', 'Prompt{{index==9}}']
        self.metadata_conditions_tags = ['Settings', 'HeaderForm', 'Prompt{{index==10}}']
        self.lims_job_tags = ['Settings', 'HeaderForm', 'Prompt{{index==11}}']

        self.display_depth_tags = ['Clients', 'DisplaySettings', 'Display#0', 'XYPlotData', 'Axes',
                                   'Axis{{Calc;FullName;value==Pressure, Digiquartz [db]}}', 'MaximumValue']

        self.display_nr_bins_tags = ['Clients', 'DisplaySettings', 'Display#0', 'XYPlotData', 'Axes',
                                     'Axis{{Calc;FullName;value==Pressure, Digiquartz [db]}}', 'MajorDivisions']

        self.display_nr_minor_bins_tags = ['Clients', 'DisplaySettings', 'Display#0', 'XYPlotData', 'Axes',
                                           'Axis{{Calc;FullName;value==Pressure, Digiquartz [db]}}', 'MinorDivisions']

        self.display_depth_tags_2 = ['Clients', 'DisplaySettings', 'Display#2', 'XYPlotData', 'Axes',
                                   'Axis{{Calc;FullName;value==Depth [salt water, m]}}', 'MaximumValue']

        self.display_nr_bins_tags_2 = ['Clients', 'DisplaySettings', 'Display#2', 'XYPlotData', 'Axes',
                                     'Axis{{Calc;FullName;value==Depth [salt water, m]}}', 'MajorDivisions']

        self.display_nr_minor_bins_tags_2 = ['Clients', 'DisplaySettings', 'Display#2', 'XYPlotData', 'Axes',
                                           'Axis{{Calc;FullName;value==Depth [salt water, m]}}', 'MinorDivisions']

        self.display_parameter_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes', 'Axis']

        self.blueprint_display_parameter_tags = ['Clients', 'DisplaySettings', 'Display', 'XYPlotData', 'Axes',
                                                 'Axis{{Calc;FullName;value==<PARAMETER>}}']

    # FiringSequence

    @property
    def auto_fire_bottles(self) -> AUTO_FIRE_DATA_DATATYPE:
        element = self._get_element_from_tag_list(self.auto_fire_bottle_tags)
        data = []
        for row in element.findall('Row'):
            data.append(row.attrib)
        return data

    @auto_fire_bottles.setter
    def auto_fire_bottles(self, data: AUTO_FIRE_DATA_DATATYPE):
        element = self._get_element_from_tag_list(self.auto_fire_bottle_tags)
        remove_child_elements(element, 'Row')
        for item in data:
            item = {key: value for key, value in item.items() if key in AUTO_FIRE_BOTTLE_KEYS}  # filter attributes
            if not sorted(item) == AUTO_FIRE_BOTTLE_KEYS:
                raise KeyError('Invalid keys found when trying to set auto fire bottles')
            element.append(get_auto_fire_bottle_row(**item))


    @property
    def auto_fire(self) -> bool:
        element = self._get_element_from_tag_list(self.auto_fire_tags)
        if element.get('FiringSequence') == '3':
            return True
        return False

    @auto_fire.setter
    def auto_fire(self, status: bool):
        firing_sequence = '1'
        if bool(status):
            firing_sequence = '3'
        element = self._get_element_from_tag_list(self.auto_fire_tags)
        element.set('FiringSequence', firing_sequence)

    @property
    def auto_fire_allow_manual_firing(self) -> bool:
        element = self._get_element_from_tag_list(self.auto_fire_data_tags)
        if element.get('AllowManualFiring') == '1':
            return True
        return False

    @auto_fire_allow_manual_firing.setter
    def auto_fire_allow_manual_firing(self, status: bool):
        allow_manual_firing = '0'
        if bool(status):
            allow_manual_firing = '1'
        element = self._get_element_from_tag_list(self.auto_fire_data_tags)
        element.set('AllowManualFiring', allow_manual_firing)

    @property
    def nr_of_water_bottles(self) -> int:
        element = self._get_element_from_tag_list(self.auto_fire_tags)
        return int(element.get('NumberOfWaterBottles'))

    @nr_of_water_bottles.setter
    def nr_of_water_bottles(self, nr: int):
        valid_nr = [12, 24]
        if nr not in valid_nr:
            raise ValueError(f'Value must be in list: {valid_nr}')
        element = self._get_element_from_tag_list(self.auto_fire_tags)
        element.set('NumberOfWaterBottles', str(nr))

    @property
    def min_pressure_or_depth(self) -> str:
        element = self._get_element_from_tag_list(self.auto_fire_data_tags)
        return element.get('MinPressureDepth')

    @min_pressure_or_depth.setter
    def min_pressure_or_depth(self, press: int | str | float):
        element = self._get_element_from_tag_list(self.auto_fire_data_tags)
        element.set('MinPressureDepth', str(press))

    @property
    def max_pressure_or_depth(self) -> str:
        element = self._get_element_from_tag_list(self.auto_fire_data_tags)
        return element.get('MaxPressureOrDepth')

    @max_pressure_or_depth.setter
    def max_pressure_or_depth(self, press: int | str | float):
        element = self._get_element_from_tag_list(self.auto_fire_data_tags)
        element.set('MaxPressureOrDepth', str(press))

    @property
    def xmlcon_path(self):
        element = self._get_element_from_tag_list(self.xmlcon_name_tags)
        return element.get('value')

    @xmlcon_path.setter
    def xmlcon_path(self, file_path):
        # file_path = file_path.strip('.xmlcon') + '.xmlcon'
        element = self._get_element_from_tag_list(self.xmlcon_name_tags)
        element.set('value', str(file_path))

    @property
    def data_path(self):
        element = self._get_element_from_tag_list(self.data_file_tags)
        return element.get('value')

    @data_path.setter
    def data_path(self, file_path):
        file_path = pathlib.Path(file_path)
        stem = file_path.stem
        directory = file_path.parent
        data_file_path = pathlib.Path(directory, f'{stem}.hex')
        element = self._get_element_from_tag_list(self.data_file_tags)
        element.set('value', str(data_file_path))

    @property
    def station(self):
        element = self._get_element_from_tag_list(self.station_tags)
        return element.get('value')

    @station.setter
    def station(self, station):
        element = self._get_element_from_tag_list(self.station_tags)
        value = f'Station: {station}'
        element.set('value', value)

    @property
    def operator(self):
        element = self._get_element_from_tag_list(self.operator_tags)
        return element.get('value')

    @operator.setter
    def operator(self, operator):
        element = self._get_element_from_tag_list(self.operator_tags)
        value = f'Operator: {operator}'
        element.set('value', value)

    @property
    def ship(self):
        element = self._get_element_from_tag_list(self.ship_tags)
        return element.get('value')

    @ship.setter
    def ship(self, ship):
        element = self._get_element_from_tag_list(self.ship_tags)
        value = f'Ship: {ship}'
        element.set('value', value)

    @property
    def cruise(self):
        element = self._get_element_from_tag_list(self.cruise_tags)
        return element.get('value')

    @cruise.setter
    def cruise(self, cruise):
        element = self._get_element_from_tag_list(self.cruise_tags)
        value = f'Cruise: {cruise}'
        element.set('value', value)

    @property
    def position(self):
        lat_element = self._get_element_from_tag_list(self.lat_tags)
        lon_element = self._get_element_from_tag_list(self.lon_tags)
        # source_element = self._get_element_from_tag_list(self.pos_source_tags)
        # return [lat_element.get('value'), lon_element.get('value'), source_element.get('value')]
        return [lat_element.get('value'), lon_element.get('value')]

    @position.setter
    def position(self, position):
        lat_element = self._get_element_from_tag_list(self.lat_tags)
        lon_element = self._get_element_from_tag_list(self.lon_tags)
        # source_element = self._get_element_from_tag_list(self.pos_source_tags)

        if len(position) == 2:
            position.append('Unknown')
        elif not position[2]:
            position.append('Unknown')

        lat_element.set('value', f'Latitude [GG MM.mm N]: {position[0]}')
        lon_element.set('value', f'Longitude [GG MM.mm E]: {position[1]}')
        # source_element.set('value', f'Position source: {position[2]}')

    @property
    def pumps(self):
        element = self._get_element_from_tag_list(self.pump_tags)
        string = element.get('value')
        return utils.metadata_string_to_dict(string.split(':', 1)[-1].strip())

    @pumps.setter
    def pumps(self, pump_ids):
        string = utils.metadata_dict_to_string(pump_ids)
        element = self._get_element_from_tag_list(self.pump_tags)
        value = f'Pumps: {string}'
        element.set('value', value)

    @property
    def event_ids(self):
        element = self._get_element_from_tag_list(self.id_tags)
        string = element.get('value')
        return utils.get_metadata_event_ids_from_string(string)
        # return utils.metadata_string_to_dict(string.split(':', 1)[-1].strip())

    @event_ids.setter
    def event_ids(self, event_ids):
        element = self._get_element_from_tag_list(self.id_tags)
        value = utils.get_metadata_string_from_event_ids(event_ids)
        element.set('value', value)

    @property
    def add_samp(self):
        element = self._get_element_from_tag_list(self.add_samp_tags)
        return element.get('value')

    @add_samp.setter
    def add_samp(self, add_samp):
        element = self._get_element_from_tag_list(self.add_samp_tags)
        value = f'Additional Sampling: {add_samp}'
        element.set('value', value)

    @property
    def metadata_admin(self):
        element = self._get_element_from_tag_list(self.metadata_admin_tags)
        string = element.get('value')
        return utils.metadata_string_to_dict(string.split(':', 1)[-1].strip())

    @metadata_admin.setter
    def metadata_admin(self, metadata_admin):
        string = utils.metadata_dict_to_string(metadata_admin)
        element = self._get_element_from_tag_list(self.metadata_admin_tags)
        value = f'Metadata admin: {string}'
        element.set('value', value)

    @property
    def metadata_conditions(self):
        element = self._get_element_from_tag_list(self.metadata_conditions_tags)
        string = element.get('value')
        return utils.metadata_string_to_dict(string)

    @metadata_conditions.setter
    def metadata_conditions(self, metadata_conditions):
        string = utils.metadata_dict_to_string(metadata_conditions)
        element = self._get_element_from_tag_list(self.metadata_conditions_tags)
        value = f'Metadata conditions: {string}'
        element.set('value', value)

    @property
    def lims_job(self):
        element = self._get_element_from_tag_list(self.lims_job_tags)
        return element.get('value')

    @lims_job.setter
    def lims_job(self, lims_job):
        element = self._get_element_from_tag_list(self.lims_job_tags)
        value = f'LIMS Job: {lims_job}'
        element.set('value', value)

    def save(self, *args, **kwargs):
        super().save(*args, space='  ', **kwargs)


def remove_child_elements(parent_element: ET.Element, tag: str) -> None:
    children = parent_element.findall(tag)
    for child in children:
        parent_element.remove(child)


def get_auto_fire_bottle_row(**kwargs) -> ET.Element:
    kw = {key: str(value) for key, value in kwargs.items()}
    return ET.Element('Row', attrib=kw)


# def get_auto_fire_bottle_row(index: str | int = None, btl_nr: str | int = None, fire_at: float | str = None) -> ET.Element:
#     attrib = dict(
#         index=str(index),
#         BottleNumber=str(btl_nr),
#         FireAt=str(fire_at)
#
#     )
#     return ET.Element('Row', attrib=attrib)
