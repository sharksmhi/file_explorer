from .logger import FileExplorerLogger
from .exporter import XlsxExporter


def create_xlsx_report(logger: FileExplorerLogger, **kwargs):
    exp = XlsxExporter(**kwargs)
    logger.export(exp)


fe_logger = FileExplorerLogger()
