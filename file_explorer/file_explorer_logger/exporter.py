from __future__ import annotations

import datetime
from abc import abstractmethod, ABC
import pathlib
from file_explorer import utils
import logging
import pandas as pd

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .logger import FileExplorerLogger


logger = logging.getLogger(__name__)


class FileExplorerLoggerExporter(ABC):

    def __init__(self, **kwargs):
        self.adm_logger = None
        self.file_path = None
        self.kwargs = kwargs

    def export(self, adm_logger: 'FileExplorerLogger'):
        self.adm_logger = adm_logger
        self._export()
        self._open_file()
        self._open_directory()

    @abstractmethod
    def _export(self):
        ...

    def _set_save_path(self, suffix):
        file_path = self.kwargs.get('file_path')
        file_name = self.kwargs.get('file_name')
        export_directory = self.kwargs.get('export_directory')
        if file_path:
            self.file_path = self.kwargs.get('path')
        else:
            if not file_name:
                date_str = datetime.datetime.now().strftime('%Y%m%d')
                ending = '-'.join(list(self.adm_logger.data.keys()))
                file_name = f'file_explorer_log_{self.adm_logger.name}_{date_str}_{ending}.xlsx'
            if not export_directory:
                export_directory = utils.get_export_directory()
            self.file_path = pathlib.Path(export_directory, file_name)
        if self.file_path.suffix != suffix:
            self.file_path = self.file_path.with_suffix(suffix)
            # self.file_path = pathlib.Path(str(self.file_path) + f'.{suffix.strip('.')}')
        if not self.file_path.parent.exists():
            raise NotADirectoryError(self.file_path.parent)

    def _open_directory(self):
        if not self.kwargs.get('open_directory'):
            return
        if not self.file_path:
            logger.info(f'open_directory is not implemented for exporter {self.__class__.__name__}')
            return
        utils.open_directory(self.file_path.parent)

    def _open_file(self):
        if not any([self.kwargs.get('open_report'), self.kwargs.get('open'), self.kwargs.get('open_file')]):
            return
        if not self.file_path:
            logger.info(f'open_file is not implemented for exporter {self.__class__.__name__}')
            return
        utils.open_file_with_default_program(self.file_path)


class XlsxExporter(FileExplorerLoggerExporter):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _export(self) -> None:
        self._set_save_path(suffix='.xlsx')
        df = self._extract_info(self.adm_logger.data)
        self._save_as_xlsx_with_table(df)
        logger.info(f'Saving file_explorer xlsx log to {self.file_path}')

    def _extract_info(self, data: dict) -> pd.DataFrame:
        info = []
        header = ['Level', 'Log type', 'Message', 'Nr of logs', 'Log number']
        if self.kwargs.get('include_items'):
            header = header + ['Item']

        for level, level_data in data.items():
            for log_type, log_type_data in level_data.items():
                for msg, msg_data in log_type_data.items():
                    count = msg_data['count']
                    log_nr = msg_data['log_nr']
                    if not self.kwargs.get('include_items') or not msg_data['items']:
                        line = [level, log_type, msg, count, log_nr]
                        info.append(line)
                        continue
                    for item in msg_data['items']:
                        # line[3] = 1
                        line = [level, log_type, msg, count, log_nr, item]
                        info.append(line)
        df = pd.DataFrame(data=info, columns=header)
        df.fillna('', inplace=True)
        if self.kwargs.get('sort_by'):
            sort_by_columns = [col for col in df.columns if
                               self._compress_item(col) in self._compress_list_items(self.kwargs.get('sort_by'))]
            df.sort_values(sort_by_columns, inplace=True)
        include_columns = header
        if self.kwargs.get('include_columns'):
            include_columns = [col for col in header if
                               self._compress_item(col) in self._compress_list_items(
                                   self.kwargs.get('include_columns'))]
        if self.kwargs.get('exclude_columns'):
            include_columns = [col for col in include_columns if
                               self._compress_item(col) not in self._compress_list_items(
                                   self.kwargs.get('exclude_columns'))]
        df = df[include_columns]
        return df

    def _compress_item(self, item: str) -> str:
        return item.lower().replace(' ', '')

    def _compress_list_items(self, lst: list[str] | str) -> list[str]:
        if type(lst) == str:
            lst = [lst]
        return [self._compress_item(item) for item in lst]

    def _save_as_xlsx_with_table(self, df: pd.DataFrame):
        """
        https://stackoverflow.com/questions/58326392/how-to-create-excel-table-with-pandas-to-excel
        """

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(str(self.file_path), engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object. Turn off the default
        # header and index and skip one row to allow us to insert a user defined
        # header.
        sheet_name = self.file_path.stem.split('SHARK_')[-1][:30]
        df.to_excel(writer, sheet_name=sheet_name, startrow=1, header=False, index=False)

        # Get the xlsxwriter workbook and worksheet objects.
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # Get the dimensions of the dataframe.
        (max_row, max_col) = df.shape

        # Create a list of column headers, to use in add_table().
        column_settings = []
        for header in df.columns:
            column_settings.append({'header': header})

        # Add the table.
        worksheet.add_table(0, 0, max_row, max_col - 1, {'columns': column_settings})

        # Make the columns wider for clarity.
        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 90)
        worksheet.set_column(3, 3, 8)
        worksheet.set_column(4, 4, 70)
        worksheet.set_column(5, 5, 70)

        # Close the Pandas Excel writer and output the Excel file.
        writer.close()


exporter_mapping = {
    'xlsx': XlsxExporter
}


def get_exporter(**kwargs):
    name = kwargs.pop('name')
    obj = exporter_mapping.get(name)
    if not obj:
        raise KeyError(f'Invalid file_explorer exporter name: {name}')
    return obj(**kwargs)