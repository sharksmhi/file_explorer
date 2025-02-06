
class FileExplorerError(Exception):
    def __init__(self, message, **kwargs):
        super().__init__(message)


class InvalidHeaderFormLine(FileExplorerError):
    pass
