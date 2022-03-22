from .xmlcon_file import XmlconFile
from file_explorer.psa.datcnv import DatCnvPSAfile


class MismatchWarning(Exception):
    def __init__(self, data=None):
        super().__init__()
        self.data = data


def get_datcnv_and_xmlcon_pars_mismatch(datcnv=None, xmlcon=None):
    dc = DatCnvPSAfile(datcnv)
    xml = XmlconFile(xmlcon)

    dc_list = [info['name'] for info in dc.get_parameter_info() if info['name'] not in ['Scan Count', 'Pump Status', 'Descent Rate [m/s]']]
    xml_list = [info['name'] for info in xml.sensor_info if info['name'] not in ['NotInUse']]

    result = {}

    xml_check_list = xml_list[:]
    for dc_name in dc_list:
        for i, xml_name in enumerate(xml_check_list[:]):
            if dc_name[:3].lower() == xml_name[:3].lower():
                xml_check_list.pop(i)
                break
    if xml_check_list:
        result['not_in_datcnv'] = xml_check_list

    dc_check_list = dc_list[:]
    for xml_name in xml_list:
        for i, dc_name in enumerate(dc_check_list[:]):
            if dc_name[:3].lower() == xml_name[:3].lower():
                dc_check_list.pop(i)
                break
    if dc_check_list:
        result['not_in_xmlcon'] = dc_check_list

    return result
