from abc import ABC, abstractmethod


class Base:
    _type = 'base'
    _name = None

    def __init__(self):
        self._content = None


class Metadata(Base, ABC):

    @abstractmethod
    def add_content(self,):
        pass