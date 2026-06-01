from __future__ import annotations
import sys
import os
import importlib
import inspect
import traceback
from abc import abstractmethod, ABC
from .dependency import Dependency
from .registry import ApplicationRegistry


class StorageInterface(ABC):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Реализуем патерн одиночка

        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(StorageInterface, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    @abstractmethod
    def add(self, key, value):
        ...

    @abstractmethod
    def get(self, key):
        ...


class EventsStorageInterface:
    ...


class EventsStorage(EventsStorageInterface, StorageInterface):
    events = {}

    def add(self, key, value):
        if key not in self.events:
            self.events.update({key: []})
        self.events[key].append(value)

    def get(self, key):
        if key not in self.events:
            return None
        return self.events[key]


Dependency(EventsStorageInterface, EventsStorage)


class Application:
    """
    В некоторых случаях бывает сложно обратиться напрямую к инстансу своей программы, например объекту
    `m = App()`. Для подобных целей существует класс Application, который позволяет из любого места любого
    пакета получить не на прямую объект приложения Muscles.

    ### Пример 1
    ```python
    from muscles import Application

    m = Application()
    type(m) # > <class App()>
    ```
    """

    _instance = None
    ref = None

    def __new__(cls, *args, ref=None, **kwargs):
        # traceback.print_stack()
        if cls._instance is None:
            cls._instance = super(Application, cls).__new__(cls, *args, **kwargs)
            setattr(cls, 'ref', ref)
        return cls._instance

    def __init__(self, *args, ref=None, **kwargs):
        self.ref = ref

    def __set__(self, instance, ref):
        self.ref = ref

    def __get__(self, instance, owner):
        return self.ref


class ApplicationMeta(type):
    """
    Реализация метакласса для создания на его основе экземпляра главного класса вашей программы

    """

    _instances = {}
    _args = ()
    _kwargs = {}

    def __call__(cls, *args, **kwargs):
        """
        Реализуем патерн одиночка

        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            instance = super(ApplicationMeta, cls).__call__(*args, **kwargs)
            if not hasattr(instance, "__muscles_registry__"):
                instance.__muscles_registry__ = ApplicationRegistry()
            initializer = getattr(instance, 'initialize', None)
            if not hasattr(instance, '_initialized') and callable(initializer):
                initializer(*args, **kwargs)
                instance._initialized = True
            cls._instances[cls] = instance
        return cls._instances[cls]

    def initialize(cls, instance, *args, **kwargs):
        """Метод инициализации, который должен быть переопределён в классах-наследниках."""
        pass

    def __init_subclass__(cls, *args, **kwargs):
        """


        :param args:
        :param kwargs:
        :return:
        """
        super().__init_subclass__()

        directory = os.getcwd()
        # Для примера создадим реестр всех наследников.
        # cls.registry.append(cls)

        if hasattr(cls, 'package_paths') and isinstance(cls.package_paths, list):
            for path in cls.package_paths:
                sys.path.append(f"{directory}/{path}")
        elif hasattr(cls, 'package_paths') and isinstance(cls.package_paths, dict):
            for item in cls.package_paths:
                # logger.debug(locale('Найден компонент {package}',
                #                     package=f"{directory}/{cls.package_paths[item]}"))
                sys.path.append(f"{directory}/{cls.package_paths[item]}")

    def __new__(cls, class_name, parents, attributes, *args, **kwargs):
        """
        Модифицируем экземпляр класса, внедряя в него дополнительные возможности

        :param class_name: Имя создаваемого класса
        :param parents: Родительские классы
        :param attributes: Атрибуты класса
        """

        # Создаем новый класс с помощью функции type
        new_class = super().__new__(cls, class_name, parents, attributes)

        # Внедрение дополнительных методов в новый класс
        setattr(new_class, 'import_package', cls.import_package)
        setattr(new_class, 'get_package_config', cls.get_package_config)
        setattr(new_class, 'init_auto_packages', cls.init_auto_packages)
        setattr(new_class, 'init_imports', cls.init_imports)

        # Инициализация методов в зависимости от структуры package_paths
        if hasattr(new_class, 'package_paths'):
            if isinstance(new_class.package_paths, list):
                for item in new_class.package_paths:
                    method_name = f'init_{item}'
                    setattr(new_class, method_name, cls.__init_structure(new_class, item))
            elif isinstance(new_class.package_paths, dict):
                for item in new_class.package_paths:
                    method_name = f'init_{item}'
                    setattr(new_class, method_name, cls.__init_structure(new_class, item))

        # Создание основного приложения с ссылкой на новый класс
        main = Application(ref=new_class)
        return new_class

    def import_package(cls, package, config=None):
        """
        Импортирует пакет `package` с последующим вызовом из импортированого
        пакета метода `init_package` с настройками `config` (Пример вызова: module.init_package(cls, config)).
        Следовательно модель/пакет должен содержать реализацию `init_package`.
        Пример:
        ```python
        self.import_package("modules.user", config={
            "package": "modules.user",
            "name": "User",
            "templates": "./templates",
            "static": "./static"
        })
        ```
        :param package: название пакета, пример modules.user
        :param config: объект конфигурации пакета
        :return:
        """
        try:
            if isinstance(sys.modules, dict):
                if package in sys.modules:
                    module = sys.modules.get(package)
                    module.__spec__.loader.exec_module(module)
                elif (spec := importlib.util.find_spec(package)) is not None:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[package] = module
                    spec.loader.exec_module(module)
                else:
                    raise Exception('Package %s not found' % package)
            if config is not None:
                module.init_package(cls, config)
        except Exception as e:
            traceback.print_exc()
            raise Exception('Package %s not found' % package)

    def get_package_config(self, package_obj: dict, init_key=None):
        """
        Преобразует и унифицирует блок конфигурации для последующего импорта.
        Пример:
        ```python
        self.get_package_config({}, init_key='user') # ->
        #{
        #    'key': 'user',
        #    'url_prefix': '/user',
        #    'templates': './templates',
        #    'static': './static'
        #}

        # или

        self.get_package_config({
            'url_prefix': '/u'
        }, init_key='user') # ->
        #{
        #    'key': 'user',
        #    'url_prefix': '/u',
        #    'templates': './templates',
        #    'static': './static'
        #}

        :param package_obj: конфигурация пакета
        :param init_key: ключ пакета
        :return:
        """
        if not package_obj:
            raise Exception('Package config not found')
        if init_key is not None and 'key' not in package_obj:
            package_obj['key'] = init_key
        if 'url_prefix' not in package_obj:
            package_obj['url_prefix'] = '/' + package_obj['key']
        if 'templates' not in package_obj:
            package_obj['templates'] = 'templates'
        if 'static' not in package_obj:
            package_obj['static'] = 'static'
        return package_obj

    def __init_structure(self, package_structure):
        def init_structure(self, config):
            for init_key in config[package_structure]:
                package = config[package_structure][init_key]
                self.import_package(package['package'], self.get_package_config(package, init_key=init_key))
        return init_structure

    def init_auto_packages(self, config, package_paths=None):
        """
        Загружает из файла конфигурации множественные пакеты.

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

        :param package_paths: List - список ключей конфигурации для импорта библиотек
        :param config: - объект конфигурации, который содержит ключи из атрибута package_paths
        :return:
        """
        if package_paths is None:
            package_paths = self.package_paths or []
        for item in package_paths:
            if item not in dict(config):
                continue
            for init_key in config[item]:
                package = config[item][init_key]
                self.import_package(package['package'], config=self.get_package_config(package, init_key=init_key))

    def init_imports(self, config):
        """
        Импортирует все пакеты из конфигурации.
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

        :param config: объект конфигурации
        :return:
        """
        if config is not None and hasattr(config, '__iter__'):
            for package in list(config):
                self.import_package(str(package))
        elif config is not None:
            for init_key in dict(config):
                package = config[init_key]
                self.import_package(package)


class PackageMeta(type):
    """
    Метакласс для создания объекта пакета.

    Часто требуется расширять функциональность программы, или выносить отдельные ее функции в другие модули и пакеты.
    Для подобных целей есть метаклас `metaclass=PackageMeta`. Инстансы основанные на нем получает возможность лучше
    взаимодействовать с основным инстансом программы.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Реализуем патерн одиночка

        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(PackageMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__()
        directory = os.getcwd()
        if hasattr(cls, 'package_paths') and isinstance(cls.package_paths, list):
            for path in cls.package_paths:
                sys.path.append(f"{directory}/{path}")
        elif hasattr(cls, 'package_paths') and isinstance(cls.package_paths, dict):
            for item in cls.package_paths:
                sys.path.append(f"{directory}/{cls.package_paths[item]}")

    def __new__(cls, class_name, parents, attributes):
        """
        Модифицируем экземпляр класса, внедряя внего дополнительные возможности

        :param class_name:
        :param parents:
        :param attributes:
        """
        # Here we could add some helper methods or attributes to c
        c = type.__new__(cls, class_name, parents, attributes)
        sys_directory = os.getcwd()
        directory = os.path.dirname(os.path.realpath(inspect.getfile(c)))
        setattr(c, 'sys_directory', sys_directory)
        setattr(c, 'directory', directory)
        setattr(c, 'import_package', cls.import_package)
        setattr(c, 'get_package_config', cls.get_package_config)
        setattr(c, 'init_auto_packages', cls.init_auto_packages)
        # for name, attr in attributes.items():
        #     if inspect.isclass(type(attr)) and isinstance(attr, Prop):
        #         setattr(attr, 'app', c)

        if hasattr(c, 'package_paths') and isinstance(c.package_paths, list):
            for item in c.package_paths:
                sys.path.append(f"{directory}/{item}")
                setattr(c, ''.join(['init_', item]), cls.__init_structure(c, item))
        elif hasattr(c, 'package_paths') and isinstance(c.package_paths, dict):
            for item in c.package_paths:
                sys.path.append(f"{directory}/{cls.package_paths[item]}")
                setattr(c, ''.join(['init_', item]), cls.__init_structure(c, item))

        return c

    def import_package(cls, package, config):
        """
        Импортирует пакет `package` с последующим вызовом из импортированого
        пакета метода `init_package` с настройками `config` (Пример вызова: module.init_package(cls, config)).
        Следовательно модель/пакет должен содержать реализацию `init_package`.
        Пример:
        ```python
        self.import_package("modules.user", config={
            "package": "modules.user",
            "name": "User",
            "templates": "./templates",
            "static": "./static"
        })
        ```
        :param package: название пакета, пример modules.user
        :param config: объект конфигурации пакета
        :return:
        """
        dir_list = package.split('.')
        spec = importlib.util.spec_from_file_location(package, '/'.join([cls.directory] + dir_list + ['__init__.py']))
        if spec is not None:
            # _package = importlib.import_module(package)
            _package = spec.loader.load_module()
            try:
                _package.init_package(cls, config)
            except Exception as e:
                # tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
                # print('!!!ERROR: ', "\n".join(tb_str))
                # traceback.print_exc()
                raise e
            except IndentationError as e:
                # tb_str = traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__)
                # print('!!!ERROR: ', "/n".join(tb_str))
                # traceback.print_exc()
                raise e
        else:
            raise Exception('Package %s not found' % package)

    def get_package_config(self, package_obj: dict, init_key=None):
        """
        Преобразует и унифицирует блок конфигурации для последующего импорта.
        Пример:
        ```python
        self.get_package_config({}, init_key='user') # ->
        #{
        #    'key': 'user',
        #    'url_prefix': '/user',
        #    'templates': './templates',
        #    'static': './static'
        #}

        # или

        self.get_package_config({
            'url_prefix': '/u'
        }, init_key='user') # ->
        #{
        #    'key': 'user',
        #    'url_prefix': '/u',
        #    'templates': './templates',
        #    'static': './static'
        #}

        :param package_obj: конфигурация пакета
        :param init_key: ключ пакета
        :return:
        """
        if not package_obj:
            raise Exception('Package configuration not found')
        if init_key is not None and 'key' not in package_obj:
            package_obj['key'] = init_key
        if 'url_prefix' not in package_obj:
            package_obj['url_prefix'] = '/' + package_obj['key']
        if 'templates' not in package_obj:
            package_obj['templates'] = 'templates'
        if 'static' not in package_obj:
            package_obj['static'] = 'static'
        return package_obj

    def __init_structure(self, package_structure):
        def init_structure(self, config):
            for init_key in config[package_structure]:
                package = config[package_structure][init_key]
                self.import_package(package['package'], self.get_package_config(package, init_key=init_key))
        return init_structure

    def init_auto_packages(self, config):
        """
        Загружает из файла конфигурации множественные пакеты.

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

        :param package_paths: List - список ключей конфигурации для импорта библиотек
        :param config: - объект конфигурации, который содержит ключи из атрибута package_paths
        :return:
        """
        for item in self.package_paths:
            if item not in config:
                continue
            for init_key in config[item]:
                package = config[item][init_key]
                self.import_package(package['package'], self.get_package_config(package, init_key=init_key))
