import re


def get_dict_from_header_form_line(line):
    """  Returns dict with attributes for a given header form line. """
    if '**' not in line:
        return

    result = dict()
    strip_line = line.strip().split('** ')[-1]
    if 'true-depth calculation' in strip_line.lower() or ':' not in strip_line:
        result['info'] = strip_line.strip()
        return result
    key, value = strip_line.split(':', 1)
    result[key.strip()] = value.strip()

    if '#' not in value:
        return result

    for item in value.split('#'):
        k, v = [part.strip() for part in item.split(':')]
        result[k] = v
    return result


def get_nmea_pos_from_header_form_line(line):
    string = line.lower()
    lat_match = re.findall('lat[:. 0-9]+', string)
    lon_match = re.findall('long[:. 0-9]+', string)
    if not (lat_match and lon_match):
        return
    lat_decmin = lat_match[0].split(' ', 1)[-1]
    lon_decmin = lon_match[0].split(' ', 1)[-1]
    if len(lon_decmin.split('.')[0].replace(' ','')) == 4:
        lon_decmin = f'0{lon_decmin}'
    return lat_decmin, lon_decmin


