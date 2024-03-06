from __future__ import annotations

import datetime
import inspect
import logging
import time
from functools import wraps

import pandas as pd

from file_explorer import event
from .exporter import FileExplorerLoggerExporter


logger = logging.getLogger(__name__)


class FileExplorerLogger:
    """Class to log events etc. in the file_explorer module"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

    WORKFLOW = 'workflow'
    METADATA = 'metadata'

    _levels = [
        DEBUG,
        INFO,
        WARNING,
        ERROR,
        CRITICAL
    ]

    _log_types = [
        WORKFLOW,
        METADATA,
        DEBUG,
        INFO,
        WARNING,
        ERROR,
        CRITICAL
    ]

    _data = dict()

    def __init__(self):
        self._initiate_log()

    def _initiate_log(self) -> None:
        """Initiate the log"""
        self._data = dict((lev, {}) for lev in self._levels)
        self._filtered_data = dict()
        self.name = ''
        self._nr_log_entries = 0

    def _check_level(self, level: str) -> str:
        level = level.lower()
        if level not in self._levels:
            msg = f'Invalid level: {level}'
            logger.error(msg)
            raise KeyError(msg)
        return level

    @property
    def data(self) -> dict:
        if self._filtered_data:
            return self._filtered_data
        return self._data

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = str(name)

    def log_workflow(self, msg: str, level: str = 'info', add: str | None = None) -> None:
        self.log(log_type=self.WORKFLOW, msg=msg, level=level, add=add)
        event.post_event('log_workflow', msg)

    def log_metadata(self, msg: str, level: str = 'info', add: str | None = None) -> None:
        self.log(log_type=self.METADATA, msg=msg, level=level, add=add)
        event.post_event('log_metadata', msg)

    def debug(self, msg: str, add: str | None = None) -> None:
        self.log(log_type=self.DEBUG, msg=msg, level=self.DEBUG, add=add)
        event.post_event('log_debug', msg)

    def info(self, msg: str, add: str | None = None) -> None:
        self.log(log_type=self.INFO, msg=msg, level=self.INFO, add=add)
        event.post_event('log_info', msg)

    def warning(self, msg: str, add: str | None = None) -> None:
        self.log(log_type=self.WARNING, msg=msg, level=self.WARNING, add=add)
        event.post_event('log_warning', msg)

    def error(self, msg: str, add: str | None = None) -> None:
        self.log(log_type=self.ERROR, msg=msg, level=self.ERROR, add=add)
        event.post_event('log_error', msg)

    def critical(self, msg: str, add: str | None = None) -> None:
        self.log(log_type=self.CRITICAL, msg=msg, level=self.CRITICAL, add=add)
        event.post_event('log_critical', msg)

    def log_time(self, func):
        """https://dev.to/kcdchennai/python-decorator-to-measure-execution-time-54hk"""
        @wraps(func)
        def timeit_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            total_time = end_time - start_time
            msg = f'{func.__name__}{args} {kwargs} took {total_time:.4f} seconds'
            self.log(log_type=self.WORKFLOW, msg=msg, level=self.DEBUG)
            event.post_event('log_workflow', msg)
            return result

        return timeit_wrapper

    def log(self, msg: str, level: str = 'info', log_type: str = 'workflow', add: str | None = None, **kwargs) -> None:
        self._nr_log_entries += 1
        level = self._check_level(level)
        self._data[level].setdefault(log_type, dict())
        # self._data[level][log_type].setdefault(msg, dict(count=0, items=[], time=datetime.datetime.now()))
        self._data[level][log_type].setdefault(msg, dict(count=0, items=[]))
        # self._data[level].setdefault(msg, 0)
        self._data[level][log_type][msg]['count'] += 1
        self._data[level][log_type][msg]['log_nr'] = self._nr_log_entries
        item = []
        if add:
            item.append(f'({self._nr_log_entries}) {add}')
        if kwargs.get('data_row'):
            item.append(f"at row {kwargs.get('data_row')}")
        if item:
            self._data[level][log_type][msg]['items'].append(' '.join(item))
        event.post_event('log', msg)

    def reset_log(self) -> 'FileExplorerLogger':
        """Resets all entries to the log"""
        logger.info(f'Resetting {self.__class__.__name__}')
        self._initiate_log()
        return self

    def reset_filter(self) -> 'FileExplorerLogger':
        self._filtered_data = dict()
        return self

    def export(self, exporter: FileExplorerLoggerExporter):
        exporter.export(self)
        return self

    def filter(self, *args,
                     log_types: str | list | None = None,
                     levels: str | list | None = None,
                     in_msg: str | None = None,
                     **kwargs) -> 'FileExplorerLogger':
        self._filtered_data = self._get_filtered_data(*args,
                                                      log_types=log_types,
                                                      levels=levels,
                                                      in_msg=in_msg,
                                                      **kwargs)
        return self

    def _get_levels(self, *args: str, levels: str | list | None = None):
        use_levels = []
        for arg in args:
            if arg.lower().strip('<>') in self._levels:
                use_levels.append(arg.lower())
        if type(levels) == str:
            levels = [levels]
        if levels:
            use_levels = list(set(use_levels + levels))
        use_levels = use_levels or self._levels
        levels_to_use = set()
        for level in use_levels:
            if '<' in level:
                levels_to_use.update(self._levels[:self._levels.index(level.strip('<>'))+1])
            elif '>' in level:
                levels_to_use.update(self._levels[self._levels.index(level.strip('<>')):])
            else:
                levels_to_use.add(level)
        return [level for level in self._levels if level in levels_to_use]

    def _get_log_types(self, *args: str, log_types: str | list | None = None):
        use_log_types = []
        for arg in args:
            if arg.lower() in self._log_types:
                use_log_types.append(arg.lower())
        if type(log_types) == str:
            log_types = [log_types]
        if log_types:
            use_log_types = list(set(use_log_types + log_types))
        use_log_types = use_log_types or self._log_types
        return use_log_types

    def _get_filtered_data(self,
                          *args,
                          log_types: str | list | None = None,
                          levels: str | list | None = None,
                          in_msg: str | None = None,
                          **kwargs
                          ) -> dict:

        log_types = self._get_log_types(*args, log_types=log_types)
        levels = self._get_levels(*args, levels=levels)

        filtered_data = dict()
        for level_name, level_data in self.data.items():
            if level_name not in levels:
                continue
            for log_type_name, log_type_data in level_data.items():
                if log_type_name not in log_types:
                    continue

                if in_msg:
                    for msg, msg_data in log_type_data.items():
                        if in_msg and in_msg.lower() not in msg.lower():
                            continue
                        filtered_data.setdefault(level_name, dict())
                        filtered_data[level_name].setdefault(log_type_name, dict())
                        filtered_data[level_name][log_type_name][msg] = msg_data
                else:
                    filtered_data.setdefault(level_name, dict())
                    filtered_data[level_name][log_type_name] = log_type_data
        return filtered_data



class old_FileExplorerLogger:
    """Class to log events etc. in the file_explorer module"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

    _levels = [
        DEBUG,
        INFO,
        WARNING,
        ERROR,
        CRITICAL
    ]


    _data = dict()

    def __init__(self):
        self._initiate_log()

    def _initiate_log(self) -> None:
        """Initiate the log"""
        self._data = dict((lev, {}) for lev in self._levels)
        self._filtered_data = dict()
        self.name = ''
        self._nr_log_entries = 0

    def _check_level(self, level: str) -> str:
        level = level.lower()
        if level not in self._levels:
            msg = f'Invalid level: {level}'
            logger.error(msg)
            raise KeyError(msg)
        return level

    @property
    def data(self) -> dict:
        if self._filtered_data:
            return self._filtered_data
        return self._data

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = str(name)

    def debug(self, msg: str, add: str | None = None) -> None:
        self.log(msg=msg, level=self.DEBUG, add=add)
        event.post_event('log_debug', msg)

    def info(self, msg: str, add: str | None = None) -> None:
        self.log(msg=msg, level=self.INFO, add=add)
        event.post_event('log_info', msg)

    def warning(self, msg: str, add: str | None = None) -> None:
        self.log(msg=msg, level=self.WARNING, add=add)
        event.post_event('log_warning', msg)

    def error(self, msg: str, add: str | None = None) -> None:
        self.log(msg=msg, level=self.ERROR, add=add)
        event.post_event('log_error', msg)

    def critical(self, msg: str, add: str | None = None) -> None:
        self.log(msg=msg, level=self.CRITICAL, add=add)
        event.post_event('log_critical', msg)

    def log_time(self, func):
        """https://dev.to/kcdchennai/python-decorator-to-measure-execution-time-54hk"""
        @wraps(func)
        def timeit_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            total_time = end_time - start_time
            msg = f'{func.__name__}{args} {kwargs} took {total_time:.4f} seconds'
            self.log(msg=msg, level=self.DEBUG)
            event.post_event('log', msg)
            return result

        return timeit_wrapper

    def log(self, msg: str, level: str = 'info', add: str | None = None, **kwargs) -> None:
        self._nr_log_entries += 1
        level = self._check_level(level)
        # self._data[level].setdefault(msg, dict(count=0, items=[], time=datetime.datetime.now()))
        self._data[level].setdefault(msg, dict(count=0, items=[]))
        # self._data[level].setdefault(msg, 0)
        self._data[level][msg]['count'] += 1
        self._data[level][msg]['log_nr'] = self._nr_log_entries
        item = []
        if add:
            item.append(f'({self._nr_log_entries}) {add}')
        if kwargs.get('data_row'):
            item.append(f"at row {kwargs.get('data_row')}")
        if item:
            self._data[level][msg]['items'].append(' '.join(item))
        event.post_event('log', msg)

    def reset_log(self) -> 'FileExplorerLogger':
        """Resets all entries to the log"""
        logger.info(f'Resetting {self.__class__.__name__}')
        self._initiate_log()
        return self

    def reset_filter(self) -> 'FileExplorerLogger':
        self._filtered_data = dict()
        return self

    def export(self, exporter: FileExplorerLoggerExporter):
        exporter.export(self)
        return self

    def filter(self, *args,
                     log_types: str | list | None = None,
                     levels: str | list | None = None,
                     in_msg: str | None = None,
                     **kwargs) -> 'FileExplorerLogger':
        self._filtered_data = self._get_filtered_data(*args,
                                                      levels=levels,
                                                      in_msg=in_msg,
                                                      **kwargs)
        return self

    def _get_levels(self, *args: str, levels: str | list | None = None):
        use_levels = []
        for arg in args:
            if arg.lower().strip('<>') in self._levels:
                use_levels.append(arg.lower())
        if type(levels) == str:
            levels = [levels]
        if levels:
            use_levels = list(set(use_levels + levels))
        use_levels = use_levels or self._levels
        levels_to_use = set()
        for level in use_levels:
            if '<' in level:
                levels_to_use.update(self._levels[:self._levels.index(level.strip('<>'))+1])
            elif '>' in level:
                levels_to_use.update(self._levels[self._levels.index(level.strip('<>')):])
            else:
                levels_to_use.add(level)

        return [level for level in self._levels if level in levels_to_use]

    def _get_filtered_data(self,
                          *args,
                          levels: str | list | None = None,
                          in_msg: str | None = None,
                          **kwargs
                          ) -> dict:

        levels = self._get_levels(*args, levels=levels)

        filtered_data = dict()
        for level_name, level_data in self.data.items():
            if level_name not in levels:
                continue
            if in_msg:
                for msg, msg_data in level_data.items():
                    if in_msg and in_msg.lower() not in msg.lower():
                        continue
                    filtered_data.setdefault(level_name, dict())
                    filtered_data[level_name][msg] = msg_data
            else:
                filtered_data.setdefault(level_name, dict())
                filtered_data[level_name] = level_data
        return filtered_data
