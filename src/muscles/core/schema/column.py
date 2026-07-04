import typing

from .field import BaseField
from .schema import Schema
from .exception import ValidationColumnException


class BaseColumn(Schema):
    column_name: typing.Optional[str]
    field_type: typing.Any
    value: typing.Any
    constructor: tuple[list[typing.Any], dict[str, typing.Any]]
    error: typing.Any

    def __set_name__(self, owner, name):
        self.column_name = name
        if not hasattr(owner, 'columns'):
            setattr(owner, 'columns', dict())
        # owner.columns[name] = self
        owner.columns.update({self.column_name: self})
        self.constructor[0][0] = name

    def __init__(self, *args, value=None, **kwargs):
        self.error = None
        if not hasattr(self, "column_name"):
            self.column_name = None
        if len(args) > 1:
            self.column_name = args[0]
            self.field_type = args[1] if not callable(args[1]) else args[1]()
        elif len(args) == 1:
            self.field_type = args[0] if not callable(args[0]) else args[0]()
        super().__init__(*args, **kwargs)
        self.value = value
        self.constructor = (
            [self.column_name, self.field_type], kwargs
        )

    def __set__(self, instance, value):
        # print("Test__set__ %s/%s-%s" % (str(self), str(instance), str(value)))
        if not hasattr(instance, '_values'):
            setattr(instance, '_values', dict())
        col = Column(*self.constructor[0], **self.constructor[1])
        try:
            value = col.field_type.setstate(value, col)
            col.value = value
            instance._values.update({self.column_name: value})
        except ValidationColumnException as vce:
            raise vce
        instance.columns.update({self.column_name: col})
        # print('__set__(%s)' % self, self.column_name, col)
        # print(instance.attributes)

    def __get__(self, instance, owner):
        if not hasattr(instance, '_values'):
            setattr(instance, '_values', dict())
        # print('__get__(%s, %s, %s)' % (str(instance), str(owner), str(self.value)), self.column_name)
        # print(self.column_name in instance._values, instance._values[self.column_name] if self.column_name in instance._values else None, instance._values)
        return instance._values[self.column_name] if self.column_name in instance._values else None

    # def __set__(self, instance, value):
    #     try:
    #         self.value = value
    #         self.validate()
    #     except ValidationColumnException as vce:
    #         self.error = vce.message
    #
    # def __get__(self, instance, owner):
    #     return self.value
    #
    # def validate(self):
    #     try:
    #         if self.value is not None:
    #             self.field_type.validate(self.value, field=self.column_name)
    #     except ValidationColumnException as vce:
    #         self.error = vce.message
    #         raise vce

    def validate(self, value=None):
        try:
            if value is not None:
                self.field_type.validate(value, field=self.column_name)
        except ValidationColumnException as vce:
            self.error = vce.message
            raise vce
        return True

    @property
    def has_error(self):
        return True if self.error is not None else False

    def dump(self) -> dict:
        return {
            self.column_name: self.field_type.dump()
        }

    def to_json(self) -> dict:
        return {
            self.column_name: self.field_type.getstate(self.value, self)
        }


class Column(BaseColumn):

    def __init__(self, *args, index=False, unique=False, primary_key=False, nullable=True, default=None,
                 required=False, title=None, description=None, example=None, min_length=None, max_length=None,
                 **kwargs):
        kwargs['index'] = index
        kwargs['unique'] = unique
        kwargs['primary_key'] = primary_key
        kwargs['nullable'] = nullable
        kwargs['default'] = default
        kwargs['required'] = required
        kwargs['title'] = title
        kwargs['description'] = description
        kwargs['example'] = example
        kwargs['min_length'] = min_length
        kwargs['max_length'] = max_length
        super().__init__(*args, **kwargs)
        if len(args) > 1:
            self.column_name = args[0]
            self.field_type = args[1] if not callable(args[1]) else args[1]()
        elif len(args) == 1:
            self.field_type = args[0] if not callable(args[0]) else args[0]()
        self.index = index
        self.unique = unique
        self.default = default
        self.required = required
        self.title = title
        self.description = description
        self.nullable = nullable
        self.value = self.default
        self.primary_key = primary_key
        self.example = example
        self.min_length = min_length
        self.max_length = max_length
        self.error = None

    # def __set__(self, instance, value):
    #     self.value = value
    #     # setattr(self.owner, self.column_name, Column(*self.constructor[0], **self.constructor[1]))
    #     self.validate()

    # def __get__(self, instance, owner):
    #     if not self.has_error:
    #         return self.value or self.default
    #     else:
    #         return None

    def validate(self, value=None):
        try:
            if not self.nullable and value is None:
                raise ValidationColumnException(self.column_name,
                                                'The value %s=%s does not nullable.' % (
                                                    self.column_name, str(value)))
            if self.required and self.value is not None:
                raise ValidationColumnException(self.column_name, 'Field %s must have a value' % self.column_name)
            if value is not None and isinstance(self.field_type, BaseField):
                self.field_type.validate(value, field=self.column_name)
            if value is not None and self.min_length is not None and len(str(value)) < self.min_length:
                raise ValidationColumnException(self.column_name, 'The length field %s of the value %s is less than %s' % (
                                                    self.column_name, str(value), str(self.min_length)
                                                ))
            if value is not None and self.max_length is not None and len(str(value)) > self.max_length:
                raise ValidationColumnException(self.column_name,
                                                'The length field %s of the value %s is greater than %s' % (
                                                    self.column_name, str(value), str(self.max_length)
                                                ))
        except ValidationColumnException as vce:
            self.error = vce.message
            raise vce
        return True

    @property
    def has_error(self):
        return True if self.error is not None else False

    def dump(self) -> dict:
        results = super().dump()
        results[self.column_name].update({
            "index": self.index,
            "unique": self.unique,
            "default": self.default,
            "required": self.required,
            "title": self.title,
            "description": self.description,
            "nullable": self.nullable,
            "value": self.value or self.default,
            "primary_key": self.primary_key,
            "example": self.example,
            "error": self.error,
        })
        return results
