import pandas as pd
from .parameter_mapping import ParameterMapping

mapping = ParameterMapping()


class Data:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    @property
    def mapped(self):
        columns = mapping.get_mapped_list(self._df.columns)
        return Data(self._df.set_axis(columns, axis=1))

    @property
    def df(self) -> pd.DataFrame:
        return self._df

    @property
    def parameters(self) -> list:
        return list(self.df)

    def __call__(self, *args, **kwargs) -> pd.DataFrame:
        return self._df

    def _check_par(self, par: str) -> str:
        if par not in self.df.columns:
            raise ValueError(f'Parameter "{par}" not in data')
        return par

    def get_par_min(self, par: str) -> float:
        return min(self.df[self._check_par(par)])

    def get_par_max(self, par: str) -> float:
        return max(self.df[self._check_par(par)])

    def get_par_range(self, par: str) -> tuple:
        return self.get_par_min(par), self.get_par_max(par)