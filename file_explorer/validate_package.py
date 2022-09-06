from file_explorer import Package
from abc import ABC, abstractmethod


class ValidatePackage(ABC):

    def __init__(self, pack: Package):
        self.pack = pack
        self.result = {}

    @abstractmethod
    def validate(self) -> dict:
        """ Returns summary of all validations in class"""
        ...


class ValidatePackageSeabird(ValidatePackage):

    def validate(self):
        pass

    def _compare_hdr_and_cnv_file(self):
        hdr = self.pack.get_file()


