from .logger import FileExplorerLogger
from .exporter import XlsxExporter


def create_xlsx_report(logger: FileExplorerLogger, filter: dict = None, **kwargs):
    if filter:
        logger.reset_filter()
        logger.filter(**filter)
    exp = XlsxExporter(**kwargs)
    logger.export(exp)


fe_logger = FileExplorerLogger()