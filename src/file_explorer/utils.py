from __future__ import annotations

import datetime
import os
import pathlib
import platform
import subprocess

EXPLORER_DIRECTORY = pathlib.Path.home() / 'file_explorer'

SHIP_TO_INTERNAL = {
    '77SE': '77_10',
    '77AR': '77_14'
}


def get_root_directory(*subfolders: str) -> pathlib.Path:
    if not EXPLORER_DIRECTORY.parent.exists():
        raise NotADirectoryError(f'Cant create root directory under {EXPLORER_DIRECTORY.parent}. Directory does not '
                                 f'exist!')
    folder = pathlib.Path(EXPLORER_DIRECTORY, *subfolders)
    folder.mkdir(exist_ok=True, parents=True)
    return folder


def get_temp_directory(*subfolders: str) -> pathlib.Path:
    temp_directory = get_root_directory() / '_temp'
    if not temp_directory.parent.exists():
        raise NotADirectoryError(f'Cant create temp directory under {temp_directory.parent}. Directory does not exist!')
    folder = pathlib.Path(temp_directory, *subfolders)
    folder.mkdir(exist_ok=True, parents=True)
    return folder


def get_config_directory(*subfolders: str) -> pathlib.Path:
    config_directory = get_root_directory() / 'config'
    if not config_directory.parent.exists():
        raise NotADirectoryError(f'Cant create config directory under {config_directory.parent}. Directory does not '
                                 f'exist!')
    folder = pathlib.Path(config_directory, *subfolders)
    folder.mkdir(exist_ok=True, parents=True)
    return folder


def get_export_directory(*subdirectories: str) -> pathlib.Path:
    export_directory = get_root_directory() / 'exports'
    if not export_directory.parent.exists():
        raise NotADirectoryError(f'Cant create export directory under {export_directory.parent}. Directory does not '
                                 f'exist!')
    # folder = pathlib.Path(export_directory, *subdirectories)
    folder = pathlib.Path(export_directory, datetime.datetime.now().strftime('%Y%m%d'), *subdirectories)
    folder.mkdir(exist_ok=True, parents=True)
    return folder


def open_file_with_default_program(path: str | pathlib.Path) -> None:
    if platform.system() == 'Darwin':       # macOS
        subprocess.call(('open', str(path)))
    elif platform.system() == 'Windows':    # Windows
        os.startfile(str(path))
    else:                                   # linux variants
        subprocess.call(('xdg-open', str(path)))


def open_file_with_excel(path: str | pathlib.Path) -> None:
    os.system(f"start EXCEL.EXE {path}")


def open_files_in_winmerge(*args: str | pathlib.Path) -> None:
    try:
        string = '"C:/Program Files/WinMerge/WinMergeU.exe"'
        for arg in args:
            string = string + f' {arg}'
        subprocess.call(string)
        # subprocess.call((f'"C:/Program Files (x86)/WinMerge/WinMergeU.exe" {file1} {file2}'))
    except:
        pass


def open_directory(*args: str | pathlib.Path) -> None:
    for arg in args:
        print(f'{arg=}')
        os.startfile(str(arg))
    try:
        for arg in args:
            os.startfile(str(arg))
    except:
        pass


def open_export_directory(*subdirectories: str) -> None:
    open_directory(get_export_directory(*subdirectories))


def get_all_class_children_list(cls):
    if not cls.__subclasses__():
        return []
    children = []
    for c in cls.__subclasses__():
        children.append(c)
        children.extend(get_all_class_children_list(c))
    return children


def get_all_class_children_names(cls):
    return [c.__name__ for c in get_all_class_children_list(cls)]
    # if not cls.__subclasses__():
    #     return []
    # names = []
    # for c in cls.__subclasses__():
    #     names.append(c.__name__)
    #     names.extend(get_all_class_children_names(c))
    # return names


def get_all_class_children(cls):
    mapping = dict()
    for c in get_all_class_children_list(cls):
        mapping[c.__name__] = c
    return mapping


def in_bbox(obj, lat_min=None, lat_max=None, lon_min=None, lon_max=None, **kwargs):
    if not any([lat_min, lat_max, lon_min, lon_max]):
        return True
    if not (obj.attributes.get('lat') and obj.attributes.get('lon')):
        return None
    lat = float(obj.attributes.get('lat'))
    lon = float(obj.attributes.get('lon'))
    if lat_min and lat_min > lat:
        return False
    if lat_max and lat_max < lat:
        return False
    if lon_min and lon_min > lon:
        return False
    if lon_max and lon_max < lon:
        return False
    return True


def in_time_span(obj, before=None, before_equal=None, after=None, after_equal=None, **kwargs):
    if not any([before, before_equal, after, after_equal]):
        return True
    dtime = obj.attributes.get('datetime')
    if not dtime:
        return None
    if before and before <= dtime:
        return False
    if before_equal and before_equal < dtime:
        return False
    if after and after >= dtime:
        return False
    if after_equal and after_equal > dtime:
        return False
    return True


def is_matching(obj, **kwargs):
    kc_ = False
    in_ = False
    if not in_bbox(obj, **kwargs):
        return False
    if not in_time_span(obj, **kwargs):
        return False
    for key, value in kwargs.items():
        if 'KC_' in key:
            key = key.replace('KC_', '')
            kc_ = True
        if 'IN_' in key:
            key = key.replace('IN_', '')
            in_ = True
        if key not in obj.attributes:
            continue
        item = obj(key.lower())
        if item and not kc_:
            if isinstance(value, str):
                value = value.lower()
            item = item.lower()
        if in_:
            if not item:
                return False
            if isinstance(value, str) and isinstance(item, str) and value not in item:
                return False
        elif item != value:
            return False
    return True


def get_internal_ship_code(code):
    c = code.upper()
    return SHIP_TO_INTERNAL.get(c, c)


def get_pos_from_comment_line(string):
    pass


def filter_packages(packages, **kwargs):
    """Filters a list of packages"""
    return_packs = []
    for pack in packages:
        if not is_matching(pack, **kwargs):
            continue
        return_packs.append(pack)
    return return_packs
