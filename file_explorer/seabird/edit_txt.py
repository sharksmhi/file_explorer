import file_explorer
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


LIMS_SHIP_MAPPING = {'77SE': '7710',
                     '7710': '7710'}


def add_event_id(txt, overwrite=False, **kwargs):
    """ Adds event_id and parent_event_id information to header form if not present """
    import ctd_processing.utils

    event_id = kwargs.get('event_id')
    parent_event_id = kwargs.get('parent_event_id')
    if not event_id and parent_event_id:
        logger.info(f'Inga event_id givna')
        return

    if isinstance(txt, file_explorer.file.InstrumentFile):
        file = txt
        path = file.path
    elif isinstance(txt, file_explorer.package.Package):
        logger.info(f'Adding event_id to package: {txt}')
        file = txt.get_file(suffix='.txt', prefix=None)
        path = file.path
    else:
        path = Path(txt)
        file = file_explorer.get_file_object_for_path(path, instrument_type='sbe')

    if path.suffix != '.txt':
        msg = f'{path} is not a txt-file'
        logger.error(msg)
        raise FileNotFoundError(msg)

    current_event_id = file('event_id')
    current_parent_event_id = file('parent_event_id')

    event_id = kwargs.get('event_id')
    parent_event_id = kwargs.get('parent_event_id')

    if current_event_id and current_event_id != event_id:
        raise ValueError(f'Current event_id: "{current_event_id}" is not the same as the one given: "{event_id}"')

    if current_parent_event_id and current_parent_event_id != parent_event_id:
        raise ValueError(f'Current parent_event_id: "{current_parent_event_id}" is not the same as the one giv'
                         f'en: "{parent_event_id}"')

    lines_before_header_form = []
    header_form_lines = []
    lines_after_header_form = []

    with open(path) as fid:
        for line in fid:
            if 'eventid' in line.lower():
                event_ids = ctd_processing.utils.get_metadata_event_ids_from_string(line.strip())
                event_ids['EventID'] = event_id
                event_ids['ParentEventID'] = parent_event_id
                line = f'//INSTRUMENT_METADATA;** ' \
                       f'{ctd_processing.utils.get_metadata_string_from_event_ids(event_ids)}\n'
                header_form_lines.append(line)
            elif line.startswith('**'):
                header_form_lines.append(line)
            elif header_form_lines:
                lines_after_header_form.append(line)
            else:
                lines_before_header_form.append(line)

        new_lines = []
        new_lines.extend(lines_before_header_form)
        new_lines.extend(header_form_lines)
        new_lines.extend(lines_after_header_form)

        export_path = path
        if not overwrite:
            export_path = Path(path.parent, f'edited_{path.name}')
        print(f'{export_path=}')

        with open(export_path, 'w') as fid:
            fid.write(''.join(new_lines))


if __name__ == '__main__':
    add_lims_job(r"C:\mw\temmp\temp_ctd_pre_system_data_root\2020\raw\SBE09_1387_20200707_1831_77SE_14_0473.bl")


