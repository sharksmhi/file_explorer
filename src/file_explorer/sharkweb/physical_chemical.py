import pandas as pd


VALUE_MAPPING = {
    'NAT Nationell miljöövervakning extra provtagning': 'EXT',
    'NAT Nationell miljöövervakning': 'NAT',
    'Sveriges meteorologiska och hydrologiska institut': 'SMHI',
    'Havs- och vattenmyndigheten': 'HAV'

}


def get_value_mapping(value):
    new_values = []
    for val in value.split(','):
        val = val.strip()
        new_values.append(VALUE_MAPPING.get(val, val))
    return ', '.join(sorted(new_values))


def get_metadata_from_sharkweb_btl_data(path, columns, **kwargs):
    """
    File requirements:
    header: "Kortnamn"
    Decimal/fältavgränsare: Punkt/tabb
    Radbtytning: Windows
    Teckenkodning: utf8
    """
    meta = {}
    mapping = {
        'SLABO_PHYSCHEM': 'SLABO',
        'STATN': 'station',
        'LATIT_DM': 'latitude',
        'LONGI_DM': 'longitude',
        'SHIPC': 'ship',
        'CRUISE_NO': 'cruise'

    }
    en = kwargs.get('encoding', 'cp1252')
    # print(f'{en=}')
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
            key = f"{d['MYEAR']}-{d['SHIPC']}-{d['VISITID'].zfill(4)}"
            if meta.get(key):
                continue
            meta[key] = {}
            for k, value in d.items():
                mapped_k = mapping.get(k, k)
                if k not in columns and mapped_k not in columns:
                    continue
                mapped_value = get_value_mapping(value)
                meta[key][k] = mapped_value
                meta[key][mapped_k] = mapped_value

            # meta[key] = {mapping.get(key, key): get_value_mapping(value) for key, value in d.items() if mapping.get(key, key) in columns}
    return meta


# This function takes longer to run....
def old_get_metadata_from_sharkweb_btl_row_data(path, columns, **kwargs):
    """
    File requirements:
    header: "Kortnamn"
    Decimal/fältavgränsare: Punkt/tabb
    Radbtytning: Windows
    Teckenkodning: Windows-1252
    """
    meta = {}
    mapping = {'SLABO_PHYSCHEM': 'SLABO'}

    df = pd.read_csv(path, sep='\t', encoding='cp1252')
    unique_key = ['MYEAR', 'SHIPC', 'VISITID']
    column_dict = {col: True for col in columns}
    meta_list = df.drop_duplicates(unique_key).to_dict('records')
    meta = {(item[unique_key[0]], item[unique_key[1]], item[unique_key[2]]):
                {key: value for key, value in item.items() if column_dict.get(key)} for item in meta_list}
    return meta


