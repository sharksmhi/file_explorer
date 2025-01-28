import logging
import os
import pathlib
import shutil
from pathlib import Path
from file_explorer import file_explorer_logger

from file_explorer import lims
from file_explorer import seabird
from file_explorer import sharkweb
from file_explorer import utils
from file_explorer.file import InstrumentFile
from file_explorer.file import UnrecognizedFile
from file_explorer.odv import odv_file
from file_explorer.other import prs_file
from file_explorer.package import MvpPackage
from file_explorer.package import OdvPackage
from file_explorer.package import Package
from file_explorer.package import PrsPackage
from file_explorer.package_collection import PackageCollection
from file_explorer.seabird import BlFile
from file_explorer.seabird import BtlFile
from file_explorer.seabird import CnvFile
from file_explorer.seabird import ConFile
from file_explorer.seabird import DatFile
from file_explorer.seabird import DeliverynoteFile
from file_explorer.seabird import HdrFile
from file_explorer.seabird import HexFile
from file_explorer.seabird import JpgFile
from file_explorer.seabird import MetadataFile
from file_explorer.seabird import PngFile
from file_explorer.seabird import RosFile
from file_explorer.seabird import SensorinfoFile
from file_explorer.seabird import TxtFile
from file_explorer.seabird import XmlFile
from file_explorer.seabird import XmlconFile
from file_explorer.seabird import ZipFile
from file_explorer.seabird import edit_hdr
from file_explorer.seabird import edit_hex
from file_explorer.seabird import header_form_file
from file_explorer.seabird import mvp_files
from file_explorer.file_explorer_logger import fe_logger

svepa_event = None
try:
    import svepa_event
except ImportError:
    fe_logger.log_workflow('Could not import svepa_event module to add svepa metadata!', level=fe_logger.ERROR)

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
        PngFile.suffix: PngFile,

        ConFile.suffix: ConFile,
        DatFile.suffix: DatFile,
        XmlFile.suffix: XmlFile,

        ZipFile.suffix: ZipFile,
        SensorinfoFile.suffix: SensorinfoFile,
        MetadataFile.suffix: MetadataFile,
        DeliverynoteFile.suffix: DeliverynoteFile,

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
    },
    'prs': {
        prs_file.PrsFile.suffix: prs_file.PrsFile
    }
}

logger.debug(f'instrument_types are: {", ".join(list(FILES))}')

PACKAGES = {
    Package.INSTRUMENT_TYPE: Package,
    MvpPackage.INSTRUMENT_TYPE: MvpPackage,
    OdvPackage.INSTRUMENT_TYPE: OdvPackage,
    PrsPackage.INSTRUMENT_TYPE: PrsPackage
}


def _get_paths_in_directory_tree(directory, stem: str = '', exclude_directory=None,
                                 exclude_suffix=None, exclude_string: str | list[str] = 'collection', suffix: str = '',
                                 **kwargs):
    """ Returns a list with all file paths in the given directory. Including all sub directories. """
    # if not any([stem, exclude_directory]):
    #     return Path(directory).glob(f'**/*{suffix}*')
    logger.debug('_get_paths_in_directory_tree')
    logger.debug(f'directory is set to: {directory}')
    logger.debug(f'stem is set to: {stem}')
    logger.debug(f'suffix is set to: {suffix}')
    match_string = kwargs.get('match_string')
    all_files = []
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            if match_string and match_string not in name:
                continue
            path = Path(root, name)
            if suffix and path.suffix.lower() != suffix.lower():
                continue
            if stem and stem.lower() not in path.stem.lower():
                continue
            all_files.append(path)
    if exclude_directory:
        logger.debug(f'exclude_directory is set to: {exclude_directory}')
        all_files = [path for path in all_files if exclude_directory not in path.parts]
    if exclude_suffix:
        logger.debug(f'exclude_suffix is set to: {exclude_suffix}')
        all_files = [path for path in all_files if path.suffix != exclude_suffix]
    if exclude_string:
        logger.debug(f'exclude_string is set to: {exclude_string}')
        if type(exclude_string) is str:
            exclude_string = [exclude_string]
        for excl in exclude_string:
            all_files = [path for path in all_files if excl.lower() not in str(path).lower()]
    return all_files


def _get_paths_in_directory(directory):
    """ Returns a list with all file paths in the given directory """
    logger.debug('_get_paths_in_directory')
    return [path for path in Path(directory).iterdir() if path.is_file()]


def get_file_object_for_path(path, instrument_type='sbe', **kwargs):
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


def get_packages_from_file_list(file_list, instrument_type='sbe', attributes=None, as_list=False, with_new_key=False, with_id_as_key=False, **kwargs):
    logger.debug('get_packages_from_file_list')
    packages = {}
    for path in file_list:
        if isinstance(path, InstrumentFile):
            file = path
        else:
            file = get_file_object_for_path(path, instrument_type=instrument_type, **kwargs)
            if not file:  # or not utils.is_matching(file, **kwargs): This check is made in get_file_object_for_path
                logger.debug(f'Could not create file object for path: {path}')
                continue
        PACK = PACKAGES.get(instrument_type)
        pack = packages.setdefault(file.pattern, PACK(attributes=attributes, **kwargs))
        file.package_instrument_type = PACK.INSTRUMENT_TYPE
        pack.add_file(file, **kwargs)
    logger.info('Setting key in packages')
    for pack in packages.values():
        pack.set_key()
    if as_list:
        packages = list(packages.values())
    elif with_new_key:
        packages = dict((item.key, item) for item in packages.values())
    elif with_id_as_key:
        packages = dict((item.id, item) for item in packages.values())
    return packages


def get_packages_in_directory(directory, as_list=False, with_new_key=False, with_id_as_key=False, exclude_directory=None, **kwargs):
    logger.debug('get_packages_in_directory')
    all_paths = _get_paths_in_directory_tree(directory, exclude_directory=exclude_directory, **kwargs)
    packages = get_packages_from_file_list(all_paths, as_list=as_list, with_new_key=with_new_key, with_id_as_key=with_id_as_key, **kwargs)
    return packages


def get_package_for_file(path, directory=None, exclude_directory=None, only_this_file=False, **kwargs):
    logger.info(f'get_package_for_file: {path}')
    if isinstance(path, InstrumentFile):
        path = path.path
    elif isinstance(path, Package):
        path = path.files[0].path
    path = Path(path)
    pack = get_packages_from_file_list([path], as_list=True, **kwargs)[0]
    if only_this_file:
        return pack

    if not directory:
        directory = path.parent
    logger.info(f'Looking for files in directory: {directory}')
    all_paths = _get_paths_in_directory_tree(directory, exclude_directory=exclude_directory)
    selected_paths = [p for p in all_paths if path.stem.lower() in p.stem.lower()]
    packages = get_packages_from_file_list(selected_paths, as_list=True, **kwargs)
    return packages[0]


def get_package_for_key(key, directory=None, exclude_directory=None, **kwargs):
    all_files = _get_paths_in_directory_tree(directory, exclude_directory=exclude_directory, **kwargs)
    packages = get_packages_from_file_list(all_files, **kwargs)
    return packages.get(key)


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


def add_path_to_package(path, pack, replace=False):
    file_obj = get_file_object_for_path(path)
    if not file_obj:
        return
    file_obj.package_instrument_type = pack.INSTRUMENT_TYPE
    pack.add_file(file_obj, replace=replace)


def update_package_with_files_in_directory(package, directory, exclude_directory=None, replace=False, **kwargs):
    logger.debug('update_package_with_files_in_directory')
    # all_files = Path(directory).glob('**/*')
    all_files = _get_paths_in_directory_tree(directory, exclude_directory=exclude_directory)
    for path in all_files:
        file = get_file_object_for_path(path, **kwargs)
        if not file:
            continue
        file.package_instrument_type = package.INSTRUMENT_TYPE
        # print('PACKAGE', package.key)
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
    """
    Copy file in file_object into directory.
    File will be renamed to its proper file name.
    Returns new InstrumentFile object.
    """
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


def rename_package(package, overwrite=False, **kwargs):
    logger.debug('rename_package')
    if not isinstance(package, Package):
        raise Exception('Given package is not a Package class')
    package.set_key()
    new_package = Package(**kwargs)
    for file in package.files:
        new_package.add_file(rename_file_object(file, overwrite=overwrite))
    return new_package


def copy_package_to_directory(pack, directory, overwrite=False, rename=False, exclude_suffix=[], **kwargs):
    """
    Copy all files in package to given directory.
    Files are renamed if rename=True.
    Returns a Package including the new file paths
    """
    logger.debug('copy_package_files_to_directory')
    if not isinstance(pack, Package):
        raise Exception(f'Given package is not of type Package: {type(pack)}')
    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)
    paths = pack.get_file_paths()
    if any([target_dir.samefile(p.parent) for p in paths]):
        raise NotADirectoryError('Can not copy files to existing file parent directory')
    target_path = None
    for source_path in paths:
        if source_path.suffix in exclude_suffix:
            continue
        if rename:
            if not pack.key:
                raise ValueError(f'Cant find key for package belonging to file: {source_path}')
            target_path = Path(target_dir, f'{pack.key}{source_path.suffix}')
        else:
            target_path = Path(target_dir, source_path.name)
        if target_path.exists() and not overwrite:
            raise FileExistsError(target_path)
        shutil.copy2(source_path, target_path)
    return get_package_for_file(target_path)


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


def edit_seabird_raw_files_in_package(pack,
                                      output_dir,
                                      overwrite_files=False,
                                      **meta):
    """
    Edits metadata in hex and hrd files. Saves to new location 'output_dir'. Option to load metadata from
    sharkweb-file or lims-file
    """
    for file in pack.get_raw_files():
        if file.suffix in ['.hdr', '.hex', '.btl', '.ros', '.xml']:
            header_form_file.update_header_form_file(file, output_directory=output_dir, overwrite_file=overwrite_files, **meta)
        else:
            target_path = pathlib.Path(output_dir, file.name)
            if target_path.exists() and not overwrite_files:
                raise FileExistsError(target_path)
            shutil.copy2(file.path, target_path)
    return get_package_for_key(pack.key, directory=output_dir)


def edit_seabird_raw_files_in_packages(packs,
                                       output_dir,
                                       from_svepa=False,
                                       sharkweb_api=False,
                                       sharkweb_file_path=None,
                                       lims_file_path=None,
                                       overwrite_files=False,
                                       columns=None,
                                       **data):
    """
    Edits metadata in hex and hrd files. Saves to new location 'output_dir'. Option to load metadata from
    sharkweb-file or lims-file
    """
    fe_logger.reset_log()
    if not columns:
        columns = seabird.METADATA_COLUMNS
    sharkweb_meta = {}
    lims_meta = {}
    if sharkweb_api:
        fe_logger.log_workflow('Downloading data from SHARKweb')
        sharkweb_meta = dict()
        all_years = sorted(set([pack.year for pack in packs]))
        file_paths = sharkweb.download_data_from_sharkweb(all_years[0], all_years[-1])
        if file_paths is None:
            fe_logger.log_workflow(f'Could not download data from SHARKweb')
        else:
            for path in file_paths:
                meta = sharkweb.get_metadata_from_sharkweb_btl_data(path, columns=columns, encoding='utf8')
                sharkweb_meta.update(meta)
    if sharkweb_file_path:
        sharkweb_meta.update(sharkweb.get_metadata_from_sharkweb_btl_data(sharkweb_file_path, columns=columns, encoding='utf8'))
    if lims_file_path:
        lims_meta = lims.get_metadata_from_lims_export_file(lims_file_path, columns=columns)
    new_packs = []
    for pack in packs:
        meta = {}

        if from_svepa and svepa_event:
            event = svepa_event.get_svepa_event('ctd', pack.datetime)
            # event = svepa.get_svepa_event('ctd', pack.datetime)
            if event:
                if hasattr(event, 'event_id'):
                    meta['event_id'] = event.event_id
                if hasattr(event, 'parent_event_id'):
                    meta['parent_event_id'] = event.parent_event_id
                if hasattr(event, 'ongoing_event_names'):
                    meta['Additional Sampling'] = ', '.join(event.ongoing_event_names)
                if hasattr(event, 'air_pres'):
                    meta['AIRPRES'] = event.air_pres
                if hasattr(event, 'air_temp'):
                    meta['AIRTEMP'] = event.air_temp
                if hasattr(event, 'wind_dir'):
                    meta['WINDIR'] = event.wind_dir
                if hasattr(event, 'wind_speed'):
                    meta['WINSP'] = event.wind_speed
                fe_logger.debug(f'Metadata after svepa: {meta}')

        fe_logger.debug(f'svepa_event: {meta=}')
        fe_logger.debug(f'{pack.short_key=}')
        meta.update(sharkweb_meta.get(pack.short_key, {}))
        fe_logger.debug(f'sharkweb: {meta=}')
        fe_logger.debug(f'Metadata after sharkweb: {meta}')
        meta.update(lims_meta.get(pack.short_key, {}))
        fe_logger.debug(f'lims: {meta=}')
        fe_logger.debug(f'Metadata after lims: {meta}')
        meta.update(data)
        fe_logger.debug(f'Metadata after "manuel meta": {meta}')
        fe_logger.debug(f'kwargs: {meta=}')

        meta = _strip_metadata_keys(meta)

        new_pack = edit_seabird_raw_files_in_package(pack,
                                                     output_dir=output_dir,
                                                     overwrite_files=overwrite_files,
                                                     **meta)
        new_packs.append(new_pack)
    return new_packs


def _strip_metadata_keys(meta: dict) -> dict:
    new_meta = {}
    for key, value in meta.items():
        new_key = key.replace('_', '')
        new_meta[new_key] = value
    return new_meta













