from abc import ABC, abstractmethod


class DataFile(ABC):
    _data_object = None

    def get_data_object(self, **kwargs):
        if self._data_object is None:
            self._data_object = self._get_data_object()
        if kwargs.get('mapped'):
            return self._data_object.mapped
        return self._data_object

    def get_data(self, **kwargs):
        data_obj = self.get_data_object(**kwargs)
        return data_obj()

    @property
    def data(self):
        return self.get_data()

    @abstractmethod
    def _get_data_object(self, **kwargs):
        ...

    def get_par_min(self, par: str, **kwargs) -> float:
        return self.get_data_object(**kwargs).get_par_min(par)

    def get_par_max(self, par: str, **kwargs) -> float:
        return self.get_data_object(**kwargs).get_par_max(par)

    def get_par_range(self, par: str, **kwargs) -> tuple:
        return self.get_data_object(**kwargs).get_par_range(par)
