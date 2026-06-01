# Перезагрузка при изменении кода

Во время разработки удобно когда сервер перезагружается сам после изменения кода. Для этого достаточно подключить объект 
`Watchdog`, путь `from muscles import Watchdog`. Так же необходимо реализовать интерфейс `WatchdogHandlerInterface`.

```python
from abc import ABC, abstractmethod


class WatchdogHandlerInterface(ABC):

    @abstractmethod
    def execute(self, event):
        pass
```


### Пример подключения `Watchdog` для перезагрузки `uwsgi`
```python
from muscles import ApplicationMeta
from muscles import Watchdog
from muscles import WatchdogHandlerInterface


class WatchdogHandler(WatchdogHandlerInterface):
    def execute(self, event):
        print("========================>Код был изменен. Перезагрузка сервера...<========================")
        import uwsgi
        return uwsgi.reload()


class App(metaclass=ApplicationMeta):
    
    # ...

    Watchdog(config={
        "path": "./",
        "config": {
            "patterns": ['*.py', '*.yaml']
        }
    }, hanler=WatchdogHandler)

    # ...

    def __init__(self):
        # импортируем библиотеки и подключаем нужные компоненты
        ...

    def __call__(self, environ, start_response):
        # return self.context.execute(environ=environ, start_response=start_response)
        ...

    def run(self):
        # self.context.execute()
        ...


```

### Сам код подключения
```python
from muscles import Watchdog
from muscles import WatchdogHandlerInterface

class WatchdogHandler(WatchdogHandlerInterface):
    def execute(self, event):
        ...

Watchdog(config={
    "path": "./",
    "config": {
        "patterns": ['*.py', '*.yaml']
    }
}, hanler=WatchdogHandler)
```
