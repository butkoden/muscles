# Создание и работа с инстансом приложения

Основная идея фреймворка Muscles это создание единой точки приложения, в данном случае этой точкой выступает класс приложения.

Создав этот объект из метакласса `metaclass=ApplicationMeta` мы получаем реализацию патерна `Singleton` с 
дополнительными плюшками. Таким образом вызывая в любом месте любого пакета объект `m = App()` мы получаем один
и тот же его экземпляр.

- `self.import_package(package, config=None)` - Импортирует пакет `package` с последующим вызовом из импортированого 
пакета метода `init_package` с настройками `config` (Пример вызова: module.init_package(cls, config)). 
Следовательно модель/пакет должен содержать реализацию `init_package`. 
Пример: `self.import_package("modules.user", config={
    "package": "modules.user", "name": "User", "templates": "./templates", "static": "./static"})`
- `self.init_auto_packages(config, package_paths=None)` - Загружает из файла конфигурации множественные пакеты.
Пример: `self.init_auto_packages(config, package_paths=['modules', 'packages'])`. 
При этом переменная `config` может выглядеть так: 
```json
{
  "modules": [
    {
      "package": "modules.user",
      "name": "User",
      "templates": "./templates",
      "static": "./static"
    }
  ],
  "packages": [
    {
      "package": "packages.oauth",
      "name": "OAuth",
      "templates": "./templates",
      "static": "./static"
    }
  ]
}
```
- `self.init_imports(config)` - Импортирует все пакеты из конфигурации.
Пример: 
```python
self.init_imports([
    {
      "package": "packages.oauth",
      "name": "OAuth",
      "templates": "./templates",
      "static": "./static"
    },
    {
      "package": "packages.clean",
      "name": "Clean",
      "templates": "./templates",
      "static": "./static"
    }
  ])
```
- `self.get_package_config(package_obj, init_key=None)` - Преобразует и унифицирует блок конфигурации для последующего 
импорта. 
Пример:
```python
self.get_package_config({}, init_key='user') 
# ->
#{
#    'key': 'user',
#    'url_prefix': '/user',
#    'templates': './templates',
#    'static': './static'
#}

# или

self.get_package_config({
    'url_prefix': '/u'
}, init_key='user') 
# ->
#{
#    'key': 'user',
#    'url_prefix': '/u',
#    'templates': './templates',
#    'static': './static'
#}
```


```python
import os
from muscles import Context, ApplicationMeta
from muscles import Configurator


class App(metaclass=ApplicationMeta):

    # Указываем необходимые конфигурационные переменные
    package_paths = ['modules']
    config_file = 'config/configuration.yaml'

    # Подключаем конфигурационные файлы @SEE configure.md
    config = Configurator(file=config_file, basedir=os.getcwd())

    # Подключаем контекст @SEE context.md
    # Для запуска необходимо реализовать класс Strategy, заложив в него нужные функции
    # Пример использования и реализаци страгии смотри в разделе cli и wsgi
    context = Context(Strategy, {})

    def __init__(self):
        """ В конструкторе объекта подключаем необходимые модули и файлы из конфигурационного файла. """
        # Подключаем пакеты из поддиректорий
        self.init_auto_packages(self.config, package_paths=self.package_paths)
        # Подключаем модели
        self.init_imports(self.config.models)
        # Подключаем модули
        for package in self.config.modules:
            self.init_imports(package.package)
        # Подключаем контроллеры
        self.init_imports(self.config.api.controllers)

    @context.before_start()
    def before_start(self):
        # before_start тригер для конеткста @SEE context.md
        pass

    @context.after_start()
    def after_start(self, result):
        # after_start тригер для конеткста @SEE context.md
        pass

    @context.context()
    def run_context(self, context):
        # context тригер для конеткста @SEE context.md
        pass

    def __call__(self, argumets):
        """ Метод для запуска стратегии контекста, которая проведет обработку запроса с параметрами argumets.
         Пример: muscles({"param": 1})
         """
        self.context.set_param('argumets', argumets)
        return self.context.execute()

    def run(self, argumets):
        """ Метод для запуска стратегии контекста, которая проведет обработку запроса с параметрами argumets.
        Пример: muscles.run({"param": 1})
        """
        self.context.set_param('argumets', argumets)
        return self.context.execute()

    
# Пример вызова
m = App()
print(m({"param": 1}))
```


## Объект Application

В некоторых случаях бывает сложно обратиться напрямую к инстансу своей программы, в нашем случае объекту `m = App()`.
Для подобных целей существует класс Application, который позволяет из любого места любого пакета получить не на прямую
объект приложения Muscles.

### Пример 1
```python
from muscles import Application

m = Application()
type(m) # > <class App()>
```


## Реализация пакета

Часто требуется расширять функциональность программы, или выносить отдельные ее функции в другие модули и пакеты.
Для подобных целей есть метаклас `metaclass=PackageMeta`. Инстансы основанные на нем получает возможноть лучше 
взаимодействовать с основным инстансом программы.

Аналогично с ApplicationMeta он содержит те же методы.


- `self.import_package(package, config=None)` - Импортирует пакет `package` с последующим вызовом из импортированого 
пакета метода `init_package` с настройками `config` (Пример вызова: module.init_package(cls, config)). 
Следовательно модель/пакет должен содержать реализацию `init_package`. 
Пример: `self.import_package("modules.user", config={
    "package": "modules.user", "name": "User", "templates": "./templates", "static": "./static"})`
- `self.init_auto_packages(config, package_paths=None)` - Загружает из файла конфигурации множественные пакеты.
Пример: `self.init_auto_packages(config, package_paths=['modules', 'packages'])`. 
При этом переменная `config` может выглядеть так: 
```json
{
  "modules": [
    {
      "package": "modules.user",
      "name": "User",
      "templates": "./templates",
      "static": "./static"
    }
  ],
  "packages": [
    {
      "package": "packages.oauth",
      "name": "OAuth",
      "templates": "./templates",
      "static": "./static"
    }
  ]
}
```
- `self.get_package_config(package_obj, init_key=None)` - Преобразует и унифицирует блок конфигурации для последующего 
импорта. 
Пример:
```python
self.get_package_config({}, init_key='user') 
# ->
#{
#    'key': 'user',
#    'url_prefix': '/user',
#    'templates': './templates',
#    'static': './static'
#}

# или

self.get_package_config({
    'url_prefix': '/u'
}, init_key='user') 
# ->
#{
#    'key': 'user',
#    'url_prefix': '/u',
#    'templates': './templates',
#    'static': './static'
#}
```

### Пример 2
```python
# instance.py
import os
from muscles import PackageMeta, Application
from muscles import Configurator


class AccountModule(metaclass=PackageMeta):
    """ Создание инстанса модуля """
    
    # Получает текущую директорию модуля/пакета
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    # Подключаем конфигурацию текущего пакета/модуля
    config_file = 'config/configuration.yaml'
    print('Config name: ', config_file)
    config = Configurator(file=config_file, basedir=dir_path)

    # Указываем ключи для импорта подмодулей или других пакетов
    package_paths = ['modules']

    # Создаем ссылку на объект инстанс главной программы
    application = Application()

    def init(self, app, config_package):
        """ Создаем конструктор пакета """
        pass



# __init__.py
def init_package(app, config_package):
    from .instance import AccountModule
    package = AccountModule()
    package.init(app, config_package)
```
