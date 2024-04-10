
SHIP_MAPPING = {
    '7710': '77SE'
}


def get_metadata_from_lims_export_file(path, columns, **kwargs):
    """
    """
    meta = {}
    column_dict = {col: True for col in columns}
    with open(path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
        header = None
        for line in fid:
            strip_line = line.strip()
            if not strip_line:
                continue
            split_line = strip_line.split(kwargs.get('sep', '\t'))
            if not header:
                header = split_line
                continue
            d = dict(zip(header, split_line))
            ship = f"{d['CTRYID']}{d['SHIPC']}"
            ship = SHIP_MAPPING.get(ship, ship)
            key = f"{d['MYEAR']}-{ship}-{d['STNNO'].zfill(4)}"
            if meta.get(key):
                continue
            meta[key] = {key: value for key, value in d.items() if column_dict.get(key)}
    return meta


def old_get_metadata_from_lims_export_file(path, columns, **kwargs):
    """
    """
    meta = {}
    with open(path, encoding=kwargs.get('encoding', 'cp1252')) as fid:
        header = None
        for line in fid:
            strip_line = line.strip()
            if not strip_line:
                continue
            split_line = strip_line.split(kwargs.get('sep', '\t'))
            if not header:
                header = split_line
                continue
            d = dict(zip(header, split_line))
            key = f"{d['MYEAR']}-{d['SHIPC']}-{d['STNNO'].zfill(4)}"
            if meta.get(key):
                continue
            meta[key] = {key: value for key, value in d.items() if key in columns}
    return meta


