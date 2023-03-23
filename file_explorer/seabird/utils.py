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


def metadata_string_to_dict(string):
    key_value = [item.strip() for item in string.split('#')]
    data = {}
    for key_val in key_value:
        key, value = [item.strip() for item in key_val.split(':')]
        data[key] = value
    return data


def metadata_dict_to_string(data):
    string_list = []
    for key, value in data.items():
        string_list.append(f'{key}: {value}')
    string = ' # '.join(string_list)
    return string


def get_metadata_string_from_event_ids(event_ids):
    string = metadata_dict_to_string(event_ids)
    return f'EventIDs: {string}'


def get_metadata_event_ids_from_string(string):
    if 'EventIDs' not in string:
        return
    return metadata_string_to_dict(string.split(':', 1)[-1].strip())


def get_header_form_information(path):
    info = {}
    with open(path) as fid:
        for line in fid:
            if not line.startswith('**'):
                continue
            split_line = [part.strip() for part in line.strip('*').split(':', 1)]
            if len(split_line) != 2:
                continue
            info[split_line[0]] = split_line[1]
            # Special treatment for metadata
            if 'metadata' in split_line[0].lower():
                metadata = metadata_string_to_dict(split_line[1])
                for key, value in metadata.items():
                    info[key] = value
    return info

