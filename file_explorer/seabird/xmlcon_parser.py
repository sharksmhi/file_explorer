import xml.etree.ElementTree as ET

from file_explorer import mapping


def get_parser_from_file(path):
    return ET.parse(path)


def get_parser_from_string(string):
    return ET.ElementTree(ET.fromstring(string))


def get_sensor_info(tree):
    index = {}
    sensor_info = []
    root = tree

    if tree.find('Instrument'):
        root = tree.find('Instrument').find('SensorArray')

    sensors = root.findall('Sensor')
    if not sensors:
        sensors = root.findall('sensor')

    ii = 0
    for i, sensor in enumerate(sensors):
        children = list(sensor)
        if not children:
            continue
        child = children[0]
        par = child.tag
        nr = child.find('SerialNumber').text
        if nr is None:
            nr = ''
        index.setdefault(par, [])
        index[par].append(ii)
        data = {'parameter': par,
                'serial_number': nr,
                'name': par}
        sensor_info.append(data)
        ii += 1
# list(cnv._xml_tree.findall('sensor')[0])[0]
    for par, index_list in index.items():
        if len(index_list) == 1:
            continue
        for nr, i in enumerate(index_list):
            sensor_info[i]['parameter'] = f'{sensor_info[i]["parameter"]}_{nr + 1}'
    return sensor_info


def get_instrument(tree):
    return mapping.get_instrument_mapping(tree.find('Instrument').find('Name').text)


def get_instrument_number(tree):
    root = tree

    if tree.find('Instrument'):
        root = tree.find('Instrument').find('SensorArray')

    sensors = root.findall('Sensor')
    if not sensors:
        sensors = root.findall('sensor')

    for sensor in sensors:
        child = list(sensor)[0]
        if child.tag == 'PressureSensor':
            return child.find('SerialNumber').text
