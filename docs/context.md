# Пример работы с контекстом


```python
from muscles import ApplicationMeta
from muscles import Context
from muscles import BaseStrategy


class WsgiStrategy(BaseStrategy):
    """ Создает новую стратегию работы с WSGI протоколом """
    def execute(self, *args, **kwargs):
        return "WSGI" # Нам важен принцип, поэтому просто возвращаем значение


class App(metaclass=ApplicationMeta):
    
    # Тут мы определяем наш контекст стратегии и передаем параметры контекста.
    context = Context(WsgiStrategy, params={})

    def __init__(self):
        self.init_auto_packages(self.config, package_paths=self.package_paths)
        self.init_imports(self.config.models)
        self.init_imports(self.config.api.controllers)

    @context.before_start()
    def before_start(self):
        """ Опредляем функцию, которая будет вызвана перед передачей в стратегию """
        print('RUN context.before_start()')

    @context.after_start()
    def after_start(self, result):
        """ Опредляем функцию, которая будет вызвана после того как стратегия обработала поток """
        print('RUN context.after_start()')

    @context.context()
    def run_context(self, context):
        """ Опредляем функцию, которая будет вызвана перед передачей в стратегию, но после before_start """
        print('RUN context.run_context()')

    def __call__(self, environ, start_response):
        """ Конда контекст и текущая стратегия определены, ее можно вызвать базовым методом execute.
        А в случае необходимости можно передать стратегии новые параметры через метод set_param(key, value).
        """
        
        self.context.set_param('environ', environ)
        self.context.set_param('start_response', start_response)
        return self.context.execute()

    def run(self):
        """ Конда контекст и текущая стратегия определены, ее можно вызвать базовым методом execute """
        self.context.execute()
```


## Логирование из проекта

Начиная с текущей версии стратегия и сервер принимают логгер из параметров контекста.
Это означает, что формат, уровень и вывод логов полностью контролируется приложением.

```python
import logging
from muscles import Context
from muscles_wsgi import WsgiStrategy

logger = logging.getLogger("butko.site")

context = Context(
    WsgiStrategy,
    options={
        "logger": logger,  # или строка с именем логгера
        "debug": False,    # True включает расширенные debug-сообщения фреймворка
    },
)
```

Также можно положить логгер в класс приложения:

```python
class App(metaclass=ApplicationMeta):
    logger = logging.getLogger("butko.site")
```

Если `logger` явно не передан, фреймворк использует именованные логгеры:

- `muscles.asgi`
- `muscles.wsgi`
