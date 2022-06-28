import datetime

INSTRUMENT = {'SBE 911plus/917plus CTD': 'SBE09',
              'SBE 19plus V2 Seacat CTD': 'SBE19',
              'SBE19plus': 'SBE19'}

SHIP = {'77se': '77SE',
        '77_10': '77SE',
        'sv': '77SE',
        'svea': '77SE',
        'argos': '77AR',
        'aranda': '34AR',
        'ar': '34AR',
        'dana': '26DA',
        'da': '26DA',
        'meri': '347V',
        'me': '347V',
        'auri': '34EB',
        'au': '34EB'}


def get_instrument_mapping(string):
    return INSTRUMENT.get(string, string)


def get_ship_mapping(string):
    return SHIP.get(string.lower(), string)


def get_year_mapping(year):
    if len(year) == 2:
        now = datetime.datetime.now().year - 2000
        if int(year) <= now:
            year = '20' + year
        else:
            year = '19' + year
    return year
