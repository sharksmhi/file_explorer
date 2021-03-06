

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
