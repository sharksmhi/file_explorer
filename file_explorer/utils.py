
def in_bbox(obj, lat_min=None, lat_max=None, lon_min=None, lon_max=None):
    if not (obj('lat') and obj('lon')):
        return None
    lat = float(obj('lat'))
    lon = float(obj('lon'))
    if lat_min and lat_min > lat:
        return False
    if lat_max and lat_max < lat:
        return False
    if lon_min and lon_min > lon:
        return False
    if lon_max and lon_max < lon:
        return False
    return True


def is_matching(obj, **kwargs):
    kc_ = False
    in_ = False
    bbox = kwargs.pop('bbox', None)
    if bbox and hasattr(obj, 'in_bbox') and not obj.in_bbox(**bbox):
        return False
    for key, value in kwargs.items():
        if 'KC_' in key:
            key = key.replace('KC_', '')
            kc_ = True
        if 'IN_' in key:
            key = key.replace('IN_', '')
            in_ = True
        item = obj(key.lower())
        if item and not kc_:
            if isinstance(value, str):
                value = value.lower()
            item = item.lower()
        if in_:
            if value and value not in item:
                return False
        elif item != value:
            return False
    return True
