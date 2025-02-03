import file_explorer
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


LIMS_SHIP_MAPPING = {'77SE': '7710',
                     '7710': '7710'}


def add_lims_job(cnv, overwrite=False):
    """ Adds LIMS job information to header form if not present """

    if isinstance(cnv, file_explorer.file.InstrumentFile):
        file = cnv
        path = file.path
    elif isinstance(cnv, file_explorer.package.Package):
        logger.info(f'Adding lims job to package: {cnv}')
        file = cnv.get_file(suffix='.cnv', prefix=None)
        path = file.path
    else:
        path = Path(cnv)
        file = file_explorer.get_file_object_for_path(path, instrument_type='sbe')

    if path.suffix != '.cnv':
        msg = f'{path} is not a cnv-file'
        logger.error(msg)
        raise FileNotFoundError(msg)

    key = 'LIMS Job:'

    year = file('year')
    if not year:
        raise ValueError(f'No year found for file: {file.path}')
    serno = file('serno')
    if not serno:
        raise ValueError(f'No serno found for file: {file.path}')
    ship = LIMS_SHIP_MAPPING.get(file('ship'))
    if ship is None:
        raise KeyError(f'No ship mapping for ship: {ship}')

    lims_job_string = f"{key} {year}{ship}-{serno}"

    lines_before_header_form = []
    header_form_lines = []
    lines_after_header_form = []

    with open(path) as fid:
        for line in fid:
            if key.lower() in line.lower():
                if lims_job_string in line:
                    return False
                else:
                    raise ValueError(f'"{lims_job_string}" not identical in line: "{line}"')
            if line.startswith('**'):
                header_form_lines.append(line)
            elif header_form_lines:
                lines_after_header_form.append(line)
            else:
                lines_before_header_form.append(line)
        header_form_lines.append(f'** {lims_job_string}\n')

        new_lines = []
        new_lines.extend(lines_before_header_form)
        new_lines.extend(header_form_lines)
        new_lines.extend(lines_after_header_form)

        export_path = path
        if not overwrite:
            export_path = Path(path.parent, f'edited_{path.name}')

        with open(export_path, 'w') as fid:
            fid.write(''.join(new_lines))


if __name__ == '__main__':
    add_lims_job(r"C:\mw\temmp\temp_ctd_pre_system_data_root\2020\raw\SBE09_1387_20200707_1831_77SE_14_0473.bl")


