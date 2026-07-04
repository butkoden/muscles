from abc import ABC, abstractmethod
from typing import Callable, Union
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler


class WatchdogHandlerInterface(ABC):

    @abstractmethod
    def execute(self, event):
        pass


class PatternMatchingHandler(PatternMatchingEventHandler):
    """Logs all the events captured."""

    def __init__(self, handler, patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False):
        super().__init__(patterns=patterns,
                         ignore_patterns=ignore_patterns,
                         ignore_directories=ignore_directories,
                         case_sensitive=case_sensitive)
        self.handler = handler

    def on_any_event(self, event):
        # print('---------:event>', event)
        # print('---------:event.event_type>', event.event_type)
        if event.is_directory:
            return
        elif event.event_type == 'modified':
            handler = self.handler()
            handler.execute(event)


class Watchdog:

    _instances = {}

    def __new__(
        cls,
        *args,
        config=None,
        handler: Union[type[WatchdogHandlerInterface], Callable[..., WatchdogHandlerInterface], None] = None,
        **kwargs,
    ):
        """
        Конструктор класса

        :param args:
        :param kwargs:
        """
        if cls not in cls._instances:
            instance = super().__new__(cls, *args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

    def __init__(
        self,
        config=None,
        handler: Union[type[WatchdogHandlerInterface], Callable[..., WatchdogHandlerInterface], None] = None,
    ):
        if config is None:
            config = {}
        event_handler = PatternMatchingHandler(handler, **(config.get('config') or {}))
        observer = Observer()
        # print('Observer path: %s' % str(config.get('path').dump()))
        # print(config.dump())
        # print('Config path: %s' % str(config.dump()))
        observer.schedule(event_handler, path=str(config.get('path')), recursive=True)
        observer.start()
