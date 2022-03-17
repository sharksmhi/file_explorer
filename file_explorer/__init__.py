import os
import shutil
from pathlib import Path
import logging

from file_explorer import utils
from file_explorer.file import InstrumentFile
from file_explorer.file import UnrecognizedFile
from file_explorer.odv import odv_file
from file_explorer.package import MvpPackage
from file_explorer.package import OdvPackage
from file_explorer.package import Package
from file_explorer.package_collection import PackageCollection
from file_explorer.seabird import BlFile
from file_explorer.seabird import BtlFile
from file_explorer.seabird import CnvFile
from file_explorer.seabird import ConFile
from file_explorer.seabird import HdrFile
from file_explorer.seabird import HexFile
from file_explorer.seabird import JpgFile
from file_explorer.seabird import RosFile
from file_explorer.seabird import TxtFile
from file_explorer.seabird import XmlconFile
from file_explorer.seabird import mvp_files
from file_explorer.seabird import DatFile
from file_explorer.seabird import XmlFile

logger = logging.getLogger(__name__)

FILES = {
    'sbe': {
        TxtFile.suffix: TxtFile,
        CnvFile.suffix: CnvFile,
        XmlconFile.suffix: XmlconFile,
        HdrFile.suffix: HdrFile,
        BlFile.suffix: BlFile,
        BtlFile.suffix: BtlFile,
        HexFile.suffix: HexFile,
        RosFile.suffix: RosFile,
        JpgFile.suffix: JpgFile,

        ConFile.suffix: ConFile,
        DatFile.suffix: DatFile,
        XmlFile.suffix: XmlFile

    },
    'mvp': {
        mvp_files.AscFile.suffix: mvp_files.AscFile,
        mvp_files.AsvpFile.suffix: mvp_files.AsvpFile,
        mvp_files.CalcFile.suffix: mvp_files.CalcFile,
        mvp_files.Em1File.suffix: mvp_files.Em1File,
        mvp_files.EngFile.suffix: mvp_files.EngFile,
        mvp_files.LogFile.suffix: mvp_files.LogFile,
        mvp_files.M1File.suffix: mvp_files.M1File,
        mvp_files.RawFile.suffix: mvp_files.RawFile,
        mvp_files.RnnFile.suffix: mvp_files.RnnFile,
        mvp_files.S10File.suffix: mvp_files.S10File,
        mvp_files.S12File.suffix: mvp_files.S12File,
        mvp_files.S52File.suffix: mvp_files.S52File,
        CnvFile.suffix: CnvFile,
    },
    'odv': {
        odv_file.OdvFile.suffix: odv_file.OdvFile
    }
}

logger.debug(f'instrument_types are: {", ".join(list(FILES))}')

PACKAGES = {
    Package.INSTRUMENT_TYPE: Package,
    MvpPackage.INSTRUMENT_TYPE: MvpPackage,
    OdvPackage.INSTRUMENT_TYPE: OdvPackage
}


def _get_paths_in_directory_tree(directory, stem='', exclude_directory=None, suffix=''):
    """ Returns a list with all file paths in the given directory. Including all sub directories. """
    # if not any([stem, exclude_directory]):
    #     return Path(directory).glob(f'**/*{suffix}*')
    logger.debug('_get_paths_in_directory_tree')
    logger.debug(f'directory is set to: {suffix}')
    logger.debug(f'stem is set to: {suffix}')
    logger.debug(f'suffix is set to: {suffix}')
    all_files = []
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            path = Path(root, name)
            if suffix and path.suffix.lower() != suffix.lower():
                continue
            if stem and stem.lower() not in path.stem.lower():
                continue
            all_files.append(path)
    if exclude_directory:
        logger.debug(f'exclude_directory is set to: {suffix}')
        all_files = [path for path in all_files if exclude_directory not in path.parts]
    return all_files


def _get_paths_in_directory(directory):
    """ Returns a list with all file paths in the given directory """
    logger.debug('_get_paths_in_directory')
    return [path for path in Path(directory).iterdir() if path.is_file()]


def get_file_object_for_path(path, instrument_type='sbe', **kwargs):
    logger.debug('get_file_object_for_path')
    path = Path(path)
    itype = FILES.get(instrument_type)
    if not itype:
        raise KeyError(f'Unknown instrument_type: {instrument_type}')
    file_cls = itype.get(path.suffix.lower())
    if not file_cls:
        logger.info(f'Unknown suffix for instrument_type: {path}')
        return False
    try:
        obj = file_cls(path, **kwargs)
        if not utils.is_matching(obj, **kwargs):
            logger.debug(f'File not matching filter: {path}')
            return None
        return obj
    except UnrecognizedFile:
        logger.warning(f'Suffix is known but still cant handle file: {path}')
        return False


def get_packages_from_file_list(file_list, instrument_type='sbe', attributes=None, **kwargs):
    logger.debug('get_packages_from_file_list')
    packages = {}
    for path in file_list:
        file = get_file_object_for_path(path, instrument_type=instrument_type)
        if not file or not utils.is_matching(file, **kwargs):
            continue
        PACK = PACKAGES.get(instrument_type)
        pack = packages.setdefault(file.pattern, PACK(attributes=attributes))
        file.package_instrument_type = PACK.INSTRUMENT_TYPE
        pack.add_file(file)
    logger.info('Setting key in packages')
    for pack in packages.values():
        pack.set_key()
    return packages


def get_packages_in_directory(directory, as_list=False, **kwargs):
    logger.debug('get_packages_in_directory')
    all_files = _get_paths_in_directory_tree(directory)
    packages = get_packages_from_file_list(all_files, **kwargs)
    if as_list:
        return list(packages.values())
    return packages


def get_package_for_file(path, directory=None, exclude_directory=None, **kwargs):
    logger.debug('get_package_for_file')
    if isinstance(path, InstrumentFile):
        path = path.path
    elif isinstance(path, Package):
        print('KEY', path.key)
        path = path.files[0].path
    path = Path(path)
    print('PATH', path)
    if not directory:
        directory = path.parent
    print('DIRECTORY', directory)
    logger.info(f'Looking for files in directory: {directory}')
    all_files = _get_paths_in_directory_tree(directory, stem=path.stem, exclude_directory=exclude_directory)
    packages = get_packages_from_file_list(all_files, **kwargs)
    print(packages)
    return packages[path.stem]


def get_file_names_in_directory(directory, suffix=None):
    logger.debug('get_file_names_in_directory')
    suffix = suffix or 'hex'
    logger.info(f'Getting files with suffix: {suffix}')
    packages = get_packages_in_directory(directory)
    paths = []
    for pack in packages.values():
        path = pack[suffix]
        if not path:
            continue
        if suffix:
            paths.append(path.name)
        else:
            paths.append(path.stem)
    return paths


def update_package_with_files_in_directory(package, directory, exclude_directory=None, replace=False):
    logger.debug('update_package_with_files_in_directory')
    # all_files = Path(directory).glob('**/*')
    all_files = _get_paths_in_directory_tree(directory, exclude_directory=exclude_directory)
    for path in all_files:
        file = get_file_object_for_path(path)
        if not file:
            continue
        file.package_instrument_type = package.INSTRUMENT_TYPE
        package.add_file(file, replace=replace)


def rename_file_object(file_object, overwrite=False):
    logger.debug('update_package_with_files_in_directory')
    current_path = file_object.path
    proper_path = file_object.get_proper_path()
    if proper_path == current_path:
        return file_object
    if proper_path.exists():
        if not overwrite:
            logger.error(f'Overwrite is set to {overwrite}')
            raise FileExistsError(proper_path)
        os.remove(proper_path)
    current_path.rename(proper_path)
    return get_file_object_for_path(proper_path)


def copy_file_object(file_object, directory=None, overwrite=False):
    logger.debug('copy_file_object')
    current_path = file_object.path
    if directory:
        target_path = Path(directory, file_object.get_proper_name())
    else:
        target_path = file_object.get_proper_path()
    if target_path == current_path:
        return file_object
    if target_path.exists():
        if not overwrite:
            raise FileExistsError(target_path)
        os.remove(target_path)
    shutil.copy2(current_path, target_path)
    return get_file_object_for_path(target_path)


def rename_package(package, overwrite=False):
    logger.debug('rename_package')
    if not isinstance(package, Package):
        raise Exception('Given package is not a Package class')
    package.set_key()
    new_package = Package()
    for file in package.files:
        new_package.add_file(rename_file_object(file, overwrite=overwrite))
    return new_package


def copy_package(package, overwrite=False):
    logger.debug('copy_package')
    if not isinstance(package, Package):
        raise Exception('Given package is not a Package class')
    package.set_key()
    new_package = Package()
    for file in package.files:
        new_package.add_file(copy_file_object(file, overwrite=overwrite))
    return new_package


def get_package_collection_for_directory(directory, instrument_type='sbe', **kwargs):
    logger.debug('get_package_collection_for_directory')
    path = Path(directory)
    packages = get_packages_in_directory(directory, as_list=True, instrument_type=instrument_type, **kwargs)
    return PackageCollection(name=path.name, packages=packages)


def get_merged_package_collections_for_packages(packages, merge_on=None, as_list=False, **kwargs):
    logger.debug('get_merged_package_collections_for_packages')
    collections = {}
    for pack in packages:
        key = pack(merge_on) or 'unknown'
        key = key.lower()
        collections.setdefault(key, PackageCollection(name=key))
        collections[key].add_package(pack)
    if as_list:
        return list(collections.values())
    return collections


def get_merged_package_collections_for_directory(directory, instrument_type='sbe', merge_on=None, **kwargs):
    logger.debug('get_merged_package_collections_for_directory')
    packages = get_packages_in_directory(directory, as_list=True, instrument_type=instrument_type, **kwargs)
    return get_merged_package_collections_for_packages(packages, merge_on=merge_on, **kwargs)


def list_unrecognized_files_in_directory(directory, instrument_type, tree=True, save_file_to_directory=False, **kwargs):
    logger.debug('list_unrecognized_files_in_directory')
    logger.info(f'tree is set to {tree}')
    if tree:
        all_paths = _get_paths_in_directory_tree(directory)
    else:
        all_paths = _get_paths_in_directory(directory)

    unrec_files = []
    for path in all_paths:
        obj = get_file_object_for_path(path, instrument_type=instrument_type, **kwargs)
        if not obj:
            unrec_files.append(str(path))

    if save_file_to_directory:
        to_directory = Path(save_file_to_directory)
        if not to_directory.exists():
            to_directory.mkdir(parents=True, exist_ok=True)
        path = Path(to_directory, f'unrecognized_files_for_instrument_type_{instrument_type}.txt')
        with open(path, 'w') as fid:
            fid.write('=' * 30)
            fid.write('\n')
            fid.write(f'Unrecognized files for instrument_type "{instrument_type}" in directory:')
            fid.write('\n')
            fid.write(f'    {directory}')
            fid.write('\n')
            fid.write('-' * 30)
            fid.write('\n')
            fid.write('\n'.join(sorted(unrec_files)))
    else:
        print('=' * 50)
        print(f'Unrecognized files for instrument_type "{instrument_type}" in directory:')
        print(f'    {directory}')
        print('-' * 50)
        for path in sorted(unrec_files):
            print(path)
        print('-' * 50)
        print()












