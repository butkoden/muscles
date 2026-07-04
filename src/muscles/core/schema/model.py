from __future__ import annotations

import typing
import uuid
from .exception import ValidationColumnException
from .schema import Schema


class BaseModel(Schema):
    __prefix__ = ""
    __collection__ = None
    columns: dict[str, typing.Any]
    _values: dict[str, typing.Any]

    def __init__(self, *args, is_new=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, "columns"):
            self.columns = {}
        if not hasattr(self, "_values"):
            self._values = {}
        if len(kwargs) > 0 and hasattr(self, 'columns'):
            for column in self.columns:
                setattr(self, column, kwargs.get(column, self.columns[column].default))
        self.is_new = is_new

    @classmethod
    def load(cls, *args, **kwargs):
        # Создаем новый экземпляр класса с is_new=False
        instance = cls(*args, is_new=False, **kwargs)
        return instance

    def validate(self):
        errors = []
        if not hasattr(self, '_values'):
            setattr(self, '_values', dict())
        for child in self.columns:
            try:
                self.columns[child].validate(value=self._values.get(child))
            except ValidationColumnException as vce:
                errors.append({self.columns[child].column_name: self.columns[child].error})
        return False if len(errors) > 0 else True

    @property
    def has_errors(self) -> bool:
        """ Вернет True если в полях присутствуют ошибки """
        errors = self.errors()
        return True if len(errors) > 0 else False

    def errors(self) -> list[dict]:
        """ Возвращает ошибки в полях """
        errors = []
        for child in self.columns:
            if self.columns[child].has_error:
                errors.append({self.columns[child].column_name: self.columns[child].error})
        return errors

    def dump(self) -> dict:
        # results = super().dump()
        results = {}
        results_ = {}
        for child in self.columns:
            if callable(self.columns[child]):
                self.columns[child] = self.columns[child]()
            results_.update(self.columns[child].dump())
        results.update({
            self.__class__.__name__: {
                "type": "object",
                "properties": results_
            }
        })
        return results

    def fields(self, exclude_fields=None) -> list:
        if exclude_fields is None:
            exclude_fields = []
        fields = []
        for child in self.columns:
            if child not in exclude_fields:
                fields.append(child)
        return fields

    def getFieldValue(self, field, default=None):
        if field in self.columns:
            value = self.columns[field].field_type.getstate(getattr(self, field, None), self.columns[field])
            return value if value else default
        else:
            raise Exception('Field "%s" not founded' % field)

    def as_dict(self, generate_uuid_function=None, exclude_fields=None):
        if exclude_fields is None:
            exclude_fields = []
        dict_field = {}
        fields = self.fields(exclude_fields=exclude_fields)
        for field in fields:
            if field in self.columns:
                field_object = self.columns[field].field_type
                dict_field[field] = field_object.getstate(getattr(self, field, None), self.columns[field])
                dict_field[field] = field_object.to_dict(dict_field[field], self.columns[field])
            # if field in self.columns and self.columns[field].field_type.schema_type == 'uuid' and self.columns[field].primary_key:
            #     dict_field[field] = uuid.UUID(str(getattr(self, field))) if getattr(self, field, None) is not None else generate_uuid_function
            # if field in self.columns and self.columns[field].field_type.schema_type == 'uuid':
            #     dict_field[field] = uuid.UUID(str(getattr(self, field))) if getattr(self, field, None) is not None else None
            #
            #
            # # elif field in self.columns and self.columns[field].data_type == 'json':
            # #     try:
            # #         dict_field[field] = json.load(getattr(self, field, None))
            # #     except Exception as e:
            # #         dict_field[field] = self.columns[field].default or {}
            # else:
            #     dict_field[field] = self.columns[field].field_type.getstate(getattr(self, field, None), self.columns[field])
            # dict_field[field] = self.columns[field].field_type.getstate(getattr(self, field, None))
                # dict_field[field] = getattr(self, field, None)
        return dict_field

    def as_list(self, generate_uuid_function=None, exclude_fields=None):
        dict_field = self.as_dict(
            generate_uuid_function=generate_uuid_function,
            exclude_fields=exclude_fields
        )
        list_field = []
        for field in dict_field:
            list_field.append(dict_field[field])
        return list_field

    def to_json(self) -> dict:
        results = {}
        results_ = {}
        for child in self.columns:
            value = self.columns[child].field_type.getstate(getattr(self, child, None), self.columns[child])
            if value is None:
                results_.update({child: None})
            else:
                results_.update({child: str(value)})
        results.update(results_)
        return results


class Model(BaseModel):

    __metaclass__ = BaseModel
    __prefix__ = ""
    __collection__ = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collection = "{prefix}{collection}".format(
            collection=self.__collection__ if self.__collection__ else self.__class__.__name__.lower(),
            prefix="%s_" % self.__prefix__ if self.__prefix__ else ''
        )

    # def __getattr__(self, name):
    #     print('-----------------__getattr__', name)
    #     if name in self.columns:
    #         print('-----------------__getattr__ columns', name, self.columns[name])
    #         return self.columns[name]
    #     else:
    #         return getattr(self, name)

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__()
        ms = ModelStorage()
        ms[cls.__name__] = cls


class ModelStorage:

    _instances: dict[str, typing.Any] = {}

    def __call__(self, *args, name: str | None = None, **kwargs):
        """
        Данная реализация не учитывает возможное изменение передаваемых
        аргументов в `__init__`.

        :param name:
        :param args:
        :param kwargs:
        :return:
        """
        key = '-'.join([str(type(self)), str(name)])
        if key not in self._instances:
            self._instances[key] = self
        return self._instances[key]

    def __init__(self, *args, **kwargs) -> None:
        """
        Конструктор класса для работы с хранилизами
        """
        if not hasattr(self, '_models'):
            self._models = {}

    @property
    def models(self) -> dict:
        """
        Вернет текущее хранилище
        """
        return self._models

    def __setitem__(self, key, value):
        """
        Провайдер для установки класса объекта в хранилище

        :param key: Ключ
        :param value: Класс
        :return:
        """
        self._models[key] = value

    def __getitem__(self, key) -> typing.Any:
        """
        Провайдер который достает и конструирует объект из класса в хранилище

        :param key: Ключ
        :return: Model
        """
        return self._models[key]

    def __contains__(self, key):
        """
        Провайдер для проверки наличия класса в хранилище

        :param key:
        :return:
        """
        return key in self._models

    def add(self, key, value):
        """
        Заносит класс объекта в хранилище с дополнительными проверками.
        Рекомендуется к использованию вместо обращения os[key] = class

        :param key: Ключ
        :param value: Класс
        :param args: Аргументы для передачи конструктору
        :param instance: Клас для проверки принадлежности
        :param kwargs: словарь для передачи конструктору объекта
        :return:
        """
        if key in self._models:
            raise Exception('ObjectStorage.add(%s, %s) -> Key already added' % (key, value))
        self._models[key] = value

    def get(self, key) -> typing.Any:
        """
        Вернет класс объекта из хранилища.
        Рекомендуется к использованию вместо обращения os[key]

        :param key:
        :return: Model
        """
        return self._models.get(key, None)
