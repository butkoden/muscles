from __future__ import annotations

import typing
import yaml
import os
import glob
import pathlib
import re
from collections import ChainMap

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ''))


def _safe_load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def _require_basedir(value: str | None) -> str:
    if value is None:
        raise TypeError("Configurator.basedir value is None. Set a current value for basedir.")
    return value


class ConfigStorage(object):
    """
    Класс хранилища созданный на основе патерна одиночка. Каждый раз при создании объекта мы получаем одиин и
    тот же его экзепляр.

    """
    _instances: dict[type["ConfigStorage"], dict[str | None, "ConfigStorage"]] = {}
    basedir: str | None = None
    secret_file: str | None = None
    active_basedir: str | None = None
    active_secret_file: str | None = None

    def __new__(cls, name: str | None = None, *args, **kwargs):
        """
        Данная реализация не учитывает возможное изменение передаваемых
        аргументов в `__init__`

        :param args:
        :param kwargs:
        :return:
        """
        if cls not in cls._instances:
            cls._instances[cls] = {}
        if name not in cls._instances[cls]:
            instance = super(ConfigStorage, cls).__new__(cls)
            cls._instances[cls][name] = instance
        return cls._instances[cls][name]


def abspath_constructor(loader, node):
    """
    Устанавливает значение abspath

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    return os.path.abspath(value)


def basedir_constructor(loader, node):
    """
    Устанавливает значение basedir

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    value = loader.construct_scalar(node)
    return configStorage.basedir


def basepath_constructor(loader, node):
    """
    Устанавливает значение basepath

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    current_basedir = _require_basedir(configStorage.basedir)
    value = loader.construct_scalar(node)
    list_path = value.split()
    list_path.insert(0, current_basedir)
    return os.path.abspath('/'.join(list_path))


def path_constructor(loader, node):
    """
    Формирует пути в значениях файла конфигурации

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    list_path = value.split()
    return os.path.abspath(os.path.join(*list_path))


def environ_constructor(loader, node):
    """
    Присоеденяет к файлу конфигурации значение из переменной окружения

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    value = value.split()
    val = os.environ.get(value[0], value[2] if len(value) == 3 and value[1] == 'or' else None)
    if val is None:
        return None
    if not isinstance(val, str):
        return val
    if val.lower() == 'true':
        return True
    elif val.lower() == 'false':
        return False
    else:
        return val


def include_constructor(loader, node):
    """
    Подключает другой файл конфигурации к основному

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    current_basedir = _require_basedir(configStorage.basedir)
    file = loader.construct_scalar(node)
    params = re.findall(r'\{([^\}]+)\}', file)
    source = os.path.join(current_basedir, file)
    if os.path.isdir(source):
        values = []
        for entry in glob.glob(os.path.join(source, '*.yaml')):
            values.append(_safe_load_yaml(entry))
        return values
    else:
        extension = ''.join(pathlib.Path(source).suffixes)
        if extension == '.yaml':
            return _safe_load_yaml(source)
        else:
            return open(source).read()


def include_dir_constructor(loader, node):
    """
    Подключает к файлу конфигурации доп. настройки из вложенной директории

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    current_basedir = _require_basedir(configStorage.basedir)
    file = loader.construct_scalar(node)
    source = os.path.join(current_basedir, file)
    if os.path.isdir(source):
        values = {}
        for entry in glob.glob(os.path.join(source, '*.yaml')):
            values.update(_safe_load_yaml(entry))
        return values
    else:
        return _safe_load_yaml(source)


def include_list_constructor(loader, node):
    """
    Загружает из дирректории файлы и присоеденяет их к конфигурации как список

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    current_basedir = _require_basedir(configStorage.basedir)
    file = loader.construct_scalar(node)
    source = os.path.join(current_basedir, file)
    if os.path.isdir(source):
        values = []
        for entry in glob.glob(os.path.join(source, '*.yaml')):
            values = values + _safe_load_yaml(entry)
        return values
    else:
        return _safe_load_yaml(source)


def secret_constructor(loader, node):
    """
    Подтягивает значение из файла secret.yaml, в котором спрятаны все важные для безопасности объекты, такие как
    пароли, ключи или другие часто повторяемые значения

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    configStorage = ConfigStorage()
    tag = loader.construct_scalar(node)
    current_basedir = _require_basedir(
        ConfigStorage.active_basedir or configStorage.basedir or ConfigStorage.basedir
    )
    secret_file = (
        ConfigStorage.active_secret_file
        or os.environ.get('CONFIG_SECRET_FILE')
        or './config/secret.yaml'
    )
    values = _safe_load_yaml(os.path.join(current_basedir, secret_file))
    return values.get(tag, None)


def permission_constructor(loader, node):
    """
    Разбивает строку в список для нужд проверки прав доступа

    :param loader: Загрузчик конструктора YAML
    :param node: значение
    :return: Откорректированное значение
    """
    value = loader.construct_scalar(node)
    list = value.split()
    return list


yaml.SafeLoader.add_constructor(u'!basedir', basedir_constructor)
yaml.SafeLoader.add_constructor(u'!basepath', basepath_constructor)
yaml.SafeLoader.add_constructor(u'!path', path_constructor)
yaml.SafeLoader.add_constructor(u'!abspath', abspath_constructor)
yaml.SafeLoader.add_constructor(u'!environ', environ_constructor)
yaml.SafeLoader.add_constructor(u'!include', include_constructor)
yaml.SafeLoader.add_constructor(u'!include_list', include_list_constructor)
yaml.SafeLoader.add_constructor(u'!include_dir', include_dir_constructor)
yaml.SafeLoader.add_constructor(u'!secret', secret_constructor)
yaml.SafeLoader.add_constructor(u'!permission', permission_constructor)


class ConfiguratorException(Exception):
    """
    Исключение для обработки конфигурации

    """
    pass


class ConfiguratorConfigFileNotFound(ValueError):
    """
    Исключение - файл конфигурации не найден

    """
    pass


class Configurator:
    """
    Класс описывает объект конфигурации

    """

    _object: typing.Any = {}
    _file: str | None = None
    iter_index = 0
    _params: dict[str, typing.Any] = {}
    _name: str | None = None
    _instance: typing.Any = None
    basedir: str | None = None

    def update_param(self, key: str, value: typing.Any) -> None:
        """
        Обновляет текущее значение параметра конфигурации

        :param key: Ключ параметра
        :param value: Значение
        :return: None
        """
        self._params.update({key: value})

    def __init__(self, obj: typing.Optional[dict] = None, file: str | None = "configuration.yaml",
                 basedir: str | None = None, name: str | None = None, secret_file: str | None = None):
        """
        Конструктор объекта конфигурации. Данный метод позволяет загрузить предопределенную конфиграцию в объект для
        данейшей работе с ним.

        :param obj: dict словарь конфигурации
        :param file: путь к файлу конфигурации
        :param basedir: установка директории проекта
        """
        configStorage = ConfigStorage(name)
        if configStorage.basedir is None and basedir is not None:
            Configurator.basedir = basedir
            configStorage.basedir = basedir
        if basedir is not None:
            ConfigStorage.basedir = basedir
        if secret_file is not None:
            configStorage.secret_file = secret_file
        # else:
        #     Configurator.basedir = os.getcwd()
        #     configStorage.basedir = os.getcwd()
        #     print('==--->configStorage2', basedir)
        try:
            self._name = name
            self._file = file
            if obj:
                self._object = obj
            else:
                try:
                    current_basedir = _require_basedir(basedir or configStorage.basedir)
                    if file is None:
                        raise TypeError("Configurator.file value is None. Set a current value for file.")
                    ConfigStorage.active_basedir = current_basedir
                    ConfigStorage.active_secret_file = secret_file
                    # print(basedir)
                    # print(self._object)
                    # print(configStorage.basedir)
                    # print(os.path.join(configStorage.basedir, file))
                    # self._object = _safe_load_yaml(os.path.join(configStorage.basedir, file))
                    self._object = _safe_load_yaml(os.path.join(current_basedir, file))
                except TypeError as e:
                    raise e
                for key in self._object.get('params', {}):
                    self._params.update({key: self._object['params'][key]})
        except ValueError as e:
            raise ConfiguratorConfigFileNotFound(e)

    def _clone(self) -> typing.Any:
        """
        Создает клон объекта

        :return: Configurator
        """
        configStorage = ConfigStorage(self._name)
        obj = type(self)(
            obj=self._object,
            file=self._file,
            basedir=self.basedir,
            name=self._name,
            secret_file=configStorage.secret_file
        )
        obj._params = self._params
        return obj

    def __getitem__(self, key):
        return self.__getattr__(key).value()

    def __getattr__(self, name):
        new_self = self._clone()
        if type(new_self._object) == dict and name in new_self._object.keys():
            new_self._object = new_self._object[name]
            return new_self
        new_self._object = None
        return new_self

    def __call__(self, *args, **kwargs):
        return self._object

    def __iter__(self):
        # h = hash(self._object)
        # if h not in self.iter_index:
        #     self.iter_index[h] = 0
        # self.iter_index[h]++
        self.iter_index = 0
        return self

    def __next__(self):
        try:
            value = self._object[self.iter_index]
        except:
            raise StopIteration
        self.iter_index += 1
        new_self = self._clone()
        new_self._object = value
        return new_self

    def __repr__(self):
        return "Configurator(%s)" % yaml.dump(self._object)

    def __str__(self):
        if isinstance(self._object, str):
            string_value = self._object
            for key in self._params:
                string_value = string_value.replace('{{' + key + '}}', str(self._params[key]))
            return string_value
        elif isinstance(self._object, type(None)):
            return ''
        elif isinstance(self._object, type(True)):
            return str(self._object)
        elif isinstance(self._object, int):
            return str(self._object)
        return "Configurator(%s)" % yaml.dump(self._object)

    def get(self, patch: str | None = None, default: typing.Optional[typing.Any] = None, with_error: bool = False) -> typing.Any:
        """
        Возвращает значение из объекта конфигурации

        :param patch: путь к значению
        :param default: вернет, если значение не будет найдено
        :param with_error: выводить ошибку в случае, если значение не будет найдено
        :return: typing.Any
        """
        if patch is None:
            return self._object
        else:
            attr = patch.split('.')
            value = self._object
            for key in attr:
                if type(value) == dict and key in value.keys():
                    value = value[key]
                elif type(value) == list and len(value) > int(key):
                    value = value[int(key)]
                else:
                    if not with_error:
                        new_self = self._clone()
                        new_self._object = default
                        return new_self
                    else:
                        raise KeyError('Path %s not found' % patch)

            new_self = self._clone()
            new_self._object = value
            return new_self

    def keys(self):
        return self._object.keys() if self._object is not None else {}

    def __len__(self):
        if isinstance(self._object, str):
            return len(self._object)
        elif isinstance(self._object, type(None)):
            return 0
        elif isinstance(self._object, type(True)):
            return 1
        elif isinstance(self._object, dict):
            return len(self._object)
        return len(self._object)

    # def __iter__(self):
    #     ''' Returns the Iterator object '''
    #     self.value = self.start - self.step
    #     return iter(self._object) if self._object else []

    def items(self):
        return ChainMap(self._object)

    def update(self, obj):
        self._object.update(obj)

    def dump(self):
        """
        Вернет строку с YAML объектом конфигурации

        :return:
        """
        return yaml.dump(self._object)

    def get_property(self, patch, default=None):
        try:
            attr = patch.split('.')
            value = self._object
            for key in attr:
                if type(value) == dict and key in value.keys():
                    value = value[key]
                elif type(value) == list and len(value) > int(key):
                    value = value[int(key)]
                else:
                    value = default
                    break

        except KeyError as e:
            value = default
            raise KeyError('Path %s not found' % patch)
        except AttributeError as e:
            value = default
            raise KeyError('Path %s not found' % patch)
        except Exception as e:
            print('ERROR Configure', e)
            value = None

        new_self = self._clone()
        new_self._object = value
        return new_self

    def value(self):
        """
        Вернет значение отчищенное от объекта конфигурации

        :return:
        """
        return self._object

    def __dict__(self):  # pyright: ignore[reportIncompatibleVariableOverride]
        """
        Вернет значение отчищенное от объекта конфигурации

        :return:
        """
        return self._object

    def get_properties(self):
        """
        Вернет значение отчищенное от объекта конфигурации

        :return:
        """
        return self._object
