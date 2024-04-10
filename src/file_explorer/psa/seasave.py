import pathlib

# from ctd_processing import utils
from file_explorer.seabird import utils
from .psa_file_with_plot import PSAfileWithPlot


class SeasavePSAfile(PSAfileWithPlot):
    def __init__(self, file_path):
        super().__init__(file_path)

        self.parameter_min_tag = 'MinimumValue'
        self.parameter_max_tag = 'MaximumValue'

        self.xmlcon_name_tags = ['Settings', 'ConfigurationFilePath']
        self.data_file_tags = ['Settings', 'DataFilePath']

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