import pandas as pd


def get_metadata_from_sharkweb_btl_row_data(path, columns, **kwargs):
    """
    File requirements:
    header: "Kortnamn"
    Decimal/fältavgränsare: Punkt/tabb
    Radbtytning: Windows
    Teckenkodning: Windows-1252
    """
    meta = {}
    mapping = {'SLABO_PHYSCHEM': 'SLABO'}
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
            meta[key] = {mapping.get(key, key): value for key, value in d.items() if mapping.get(key, key) in columns}
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


