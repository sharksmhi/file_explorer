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

    elif tree.find('InstrumentState'):
        root = tree.find('InstrumentState').find('HardwareData').find('InternalSensors')

    sensors = root.findall('Sensor')
    if not sensors:
        sensors = root.findall('sensor')

    ii = 0
    for i, sensor in enumerate(sensors):
        nr = ''
        par = ''
        typ = ''
        children = list(sensor)
        if not children:
            continue
        if len(children) > 1:
            par = sensor.attrib['id']
            for child in children:
                if child.tag == 'type':
                    typ = child.text
                elif child.tag == 'SerialNumber':
                    nr = child.text
        else:
            child = children[0]
            par = child.tag
            if par == 'Sensor':
                par = child.attrib['id']
            nr = child.find('SerialNumber').text
            if nr is None:
                nr = ''
        index.setdefault(par, [])
        index[par].append(ii)
        data = {'parameter': par,
                'serial_number': nr,
                'name': par,
                'type': typ}
        sensor_info.append(data)
        ii += 1
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


def get_hardware_data(tree):
    item = tree.find('InstrumentState').find('HardwareData')
    if not item:
        return
    return item.attrib
