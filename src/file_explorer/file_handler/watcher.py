import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import logging
import pathlib


logger = logging.getLogger(__name__)

watch_subscribers = {}


def _trigger_folder_updated(_id: str, data: dict, *args, **kwargs):
    for func in watch_subscribers.get(_id, []):
        func(data)


def _add_watch_of_folder(_id: str, func):
    watch_subscribers.setdefault(_id, [])
    watch_subscribers[_id].append(func)


class Watcher:

    def __init__(self, watch_directory, _id):
        self._directory = watch_directory
        self._id = _id
        self._observer = Observer()

        self._thread = None

    def run(self):
        if self._thread:
            logger.warning(f'Thread for watcher {self._id} is already running!')
            return 
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        event_handler = EventHandler(_id=self._id)
        self._observer.schedule(event_handler, self._directory, recursive=True)
        self._observer.start()
        try:
            while True:
                time.sleep(1)
        except:
            self._observer.stop()
            print("Observer Stopped")

        self._observer.join()

    def stop(self):
        self._thread.join()
        self._thread = None


class EventHandler(FileSystemEventHandler):

    def __init__(self, _id):
        self._id = _id

    def on_any_event(self, event):
        if event.is_directory:
            return None
        data = dict(
            event=event,
            src_path=pathlib.Path(event.src_path),
            dest_path=None,
            event_type=event.event_type,
            id=self._id
        )
        if event.event_type == 'moved':
            data['dest_path'] = pathlib.Path(event.dest_path)
        _trigger_folder_updated(_id=self._id, data=data)


def keep_watch_of_folder(folder=None, id=None, func=None):
    _add_watch_of_folder(id, func)
    watcher = Watcher(folder, id)
    watcher.run()
    return watcher


