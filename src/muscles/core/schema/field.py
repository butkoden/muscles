import datetime
import json
import re
import json as jsonLib
import uuid
from typing import Union

from .schema import Schema
from ..schema.exception import ValidationColumnException
from .value_object import ValueObject


class BaseField(Schema):
    schema_type = None
    data_type = None
    data_format = None

    def __init__(self, *args, **kwargs):
        self.error = None
        if self.schema_type is None:
            self.schema_type = self.data_type
        super().__init__(*args, **kwargs)

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "data_type": self.data_type,
            "type": self.schema_type,
            "pattern": self.data_format,
        })
        return results

    def to_json(self) -> dict:
        return self

    def getstate(self, value, column) -> dict:
        if value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def setstate(self, value, column) -> dict:
        if value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def validate_data_format(self, value, message):
        if self.data_format is not None and not re.match(self.data_format, str(value)):
            raise ValidationColumnException(self.schema_type, message)
        return True

    def validate(self, value, field=None):
        return self.validate_data_format(value, 'The value %s=%s does not match the field format' % (str(field), str(value)))

    def to_dict(self, value, column):
        if value is None:
            return None
        elif isinstance(value, int):
            return value
        else:
            return str(value)

    def from_dict(self, value, column):
        return value


class Boolean(BaseField):
    data_type = 'boolean'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, value, field=None):
        if not isinstance(value, bool):
            raise ValidationColumnException(self.schema_type, 'The value of %s=%s is not boolean' % (
                                         str(field), str(value)
                ))
        return True


class List(BaseField):
    data_type = 'array'

    def __init__(self, *args, **kwargs):
        self._items = args[0] if len(args) > 0 else None
        super().__init__(*args, **kwargs)

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "items": [self._items.dump()] if self._items else {},
        })
        return results

    def validate(self, value, field=None):
        if not isinstance(value, list):
            raise ValidationColumnException(self.schema_type, 'The value of %s=%s is not a list' % (
                                         str(field), str(value)
            ))
        return True

    def setstate(self, value, column) -> dict:
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, int):
            value = [value]
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def getstate(self, value, column) -> datetime:
        if isinstance(value, str):
            value = [value]
        elif isinstance(value, int):
            value = [value]
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def to_dict(self, value, column):
        return value

    def from_dict(self, value, column):
        return value


class Numeric(BaseField):
    data_type = 'number'
    data_format = r'^\d+$'

    def __init__(self, *args, precision=None, scale=None, decimal_return_scale=None, asdecimal=True, **kwargs):
        kwargs['precision'] = precision
        kwargs['scale'] = scale
        kwargs['decimal_return_scale'] = decimal_return_scale
        kwargs['asdecimal'] = asdecimal
        super().__init__(*args, **kwargs)
        self.precision = precision
        self.scale = scale
        self.decimal_return_scale = decimal_return_scale
        self.asdecimal = asdecimal

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "precision": self.precision,
            "scale": self.scale,
            "decimal_return_scale": self.decimal_return_scale,
            "asdecimal": self.asdecimal,
        })
        return results

    def validate(self, value, field=None):
        self.validate_data_format(value, 'Value %s=%s is not numerical.' % (
                                                str(field), str(value)
                                  ))
        if not isinstance(value, str) and not isinstance(value, (int, float)):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not numeric' % (
                                                str(field), str(value)
                                  ))
        return True


class Float(BaseField):
    data_type = 'float'

    def __init__(self, *args, precision=None, decimal_return_scale=None, asdecimal=True, **kwargs):
        kwargs['precision'] = precision
        kwargs['decimal_return_scale'] = decimal_return_scale
        kwargs['asdecimal'] = asdecimal
        super().__init__(*args, **kwargs)
        self.precision = precision
        self.asdecimal = asdecimal
        self.decimal_return_scale = decimal_return_scale

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "precision": self.precision,
            "decimal_return_scale": self.decimal_return_scale,
            "asdecimal": self.asdecimal,
        })
        return results

    def validate(self, value, field=None):
        if not isinstance(value, float):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not numeric' % (
                                                str(field), str(value)
                                  ))
        return True


class Double(BaseField):
    data_type = 'double'

    def __init__(self, *args, precision=None, decimal_return_scale=None, asdecimal=True, **kwargs):
        kwargs['precision'] = precision
        kwargs['decimal_return_scale'] = decimal_return_scale
        kwargs['asdecimal'] = asdecimal
        super().__init__(*args, **kwargs)
        self.precision = precision
        self.asdecimal = asdecimal
        self.decimal_return_scale = decimal_return_scale

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "precision": self.precision,
            "decimal_return_scale": self.decimal_return_scale,
            "asdecimal": self.asdecimal,
        })
        return results

    def validate(self, value, field=None):
        if not re.match(r"\d+(\.\d+)?", str(value)):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not double' % (
                                                str(field), str(value)
                                  ))
        return True


class Binary(BaseField):
    data_type = 'binary'

    def __init__(self, *args, length=None, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "length": self.length,
        })
        return results

    def validate(self, value, field=None):
        if not isinstance(value, bytes):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a byte value' % (
                                                str(field), str(value)
                                  ))
        return True


class Enum(BaseField):
    schema_type = 'string'
    data_type = 'enum'

    def __set_name__(self, owner, name):
        self.enum_name = name

    def __init__(self, *args, enum=None, **kwargs):
        if enum is None:
            enum = []
        kwargs['enum'] = enum
        super().__init__(*args, **kwargs)
        self.enum = enum

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "enum": self.enum,
        })
        return results

    def validate(self, value, field=None):
        if value not in self.enum:
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s does not match any of the possible values' % (
                                                str(field), str(value)
                                  ))
        return True


class Key(BaseField):
    data_type = 'key'

    def dump(self) -> dict:
        results = super().dump()
        results["type"] = "big_integer"
        return results


class UUID4(BaseField):
    data_type = 'uuid'
    data_format = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[8-9a-fA-F][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def dump(self) -> dict:
        results = super().dump()
        results["type"] = "string"
        return results

    def getstate(self, value, column) -> Union[None, uuid.UUID]:
        if value in ('generate_uuid4', 'gen'):
            value = uuid.uuid4()
        elif callable(value):
            value = value()
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        elif value is not None and isinstance(value, str):
            value = uuid.UUID(str(value))
        return value

    def setstate(self, value, column) -> Union[None, uuid.UUID]:
        if value in ('generate_uuid4', 'gen'):
            value = uuid.uuid4()
        elif callable(value):
            value = value()
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        elif value is not None and isinstance(value, str):
            value = uuid.UUID(str(value))
        return value

    def validate(self, value, field=None):
        self.validate_data_format(value, 'The value %s=%s does not match the format of the field' % (
                                                str(field), str(value)
                                  ))
        return True


class BigInteger(BaseField):
    data_type = 'big_integer'

    def __init__(self, *args, length=None, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "length": self.length,
        })
        return results

    def validate(self, value, field=None):
        if not isinstance(value, int):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a number' % (
                                                str(field), str(value)
                                  ))
        return True


class SmallInteger(BigInteger):
    data_type = 'small_integer'

    def __init__(self, *args, length=None, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def validate(self, value, field=None):
        if not isinstance(value, int) or -5 <= value <= 256:
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s does not match the range of digits from -5 to 256' % (
                                                str(field), str(value)
                                  ))
        return True


class Integer(BigInteger):
    data_type = 'integer'

    def __init__(self, *args, length=None, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def validate(self, value, field=None):
        if not isinstance(value, int):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a number' % (
                                                str(field), str(value)
                                  ))
        return True


class String(BaseField):
    data_type = 'string'

    def __init__(self, *args, length=255, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "length": self.length,
        })
        return results

    def validate(self, value, field=None):
        if not isinstance(value, str):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a string' % (
                                                str(field), str(value)
                                  ))
        return True


class Json(BaseField):
    data_type = 'json'

    def __init__(self, *args, length=56000, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "length": self.length,
        })
        return results

    def getstate(self, value, column) -> dict:
        if value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        try:
            return json.load(value)
        except Exception as e:
            return {}

    def setstate(self, value, column) -> dict:
        if value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return jsonLib.dumps(value)

    def get_dict(self, value, column):
        return value


class File(BaseField):
    data_type = 'file'
    schema_type = 'string'
    data_format = 'binary'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Date(BaseField):
    data_type = 'date'
    def setstate(self, value, column) -> dict:
        if value == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif callable(value):
            value = value()
        elif column.default == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def getstate(self, value, column) -> datetime:
        if value == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif callable(value):
            value = value()
        elif column.default == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def to_dict(self, value, column):
        return value.strftime("%Y-%m-%d") if isinstance(value, datetime.datetime) else value

    def from_dict(self, value, column):
        return value


class DateTime(BaseField):
    data_type = 'date_time'

    def __init__(self, *args, timezone=None, **kwargs):
        kwargs['timezone'] = timezone
        super().__init__(*args, **kwargs)
        self.timezone = timezone

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "timezone": self.timezone,
        })
        return results

    def setstate(self, value, column) -> dict:
        if value == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif callable(value):
            value = value()
        elif column.default == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def getstate(self, value, column) -> datetime:
        if value == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif callable(value):
            value = value()
        elif column.default == 'now':
            value = datetime.datetime.now(tz=self.timezone)
        elif value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        return value

    def to_dict(self, value, column):
        return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime.datetime) else value

    def from_dict(self, value, column):
        return value


class Timestamp(DateTime):
    data_type = 'timestamp'

    def __init__(self, *args, timezone=None, **kwargs):
        kwargs['timezone'] = timezone
        super().__init__(*args, **kwargs)
        self.timezone = timezone

    def to_dict(self, value, column):
        return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime.datetime) else value

    def from_dict(self, value, column):
        return value



class Time(DateTime):
    data_type = 'time'

    def __init__(self, *args, timezone=None, **kwargs):
        kwargs['timezone'] = timezone
        super().__init__(*args, **kwargs)
        self.timezone = timezone


class Text(String):
    data_type = 'string'

    def __init__(self, *args, length=65535, **kwargs):
        kwargs['length'] = length
        super().__init__(*args, **kwargs)
        self.length = length

    def validate(self, value, field=None):
        if not isinstance(value, str):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a string' % (
                                                str(field), str(value)
                                  ))
        return True


class ValueObjectField(BaseField):
    data_type = "value_object"
    schema_type = "string"

    def __init__(self, *args, value_object_class=None, **kwargs):
        super().__init__(*args, **kwargs)
        if value_object_class is None:
            raise ValueError("value_object_class is required for ValueObjectField")
        if not issubclass(value_object_class, ValueObject):
            raise TypeError("value_object_class must be a ValueObject subclass")
        self.value_object_class = value_object_class

    def dump(self) -> dict:
        results = super().dump()
        results.update({
            "value_object": self.value_object_class.__name__,
        })
        return results

    def setstate(self, value, column):
        if value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        if value is None:
            return None
        return self.value_object_class.parse(value)

    def getstate(self, value, column):
        if value is None and callable(column.default):
            value = column.default()
        elif value is None:
            value = column.default
        if value is None:
            return None
        return self.value_object_class.parse(value)

    def validate(self, value, field=None):
        try:
            self.value_object_class.parse(value)
        except Exception as exc:
            raise ValidationColumnException(
                self.schema_type,
                f"The value {field}={value} is not valid for {self.value_object_class.__name__}: {exc}",
            )
        return True

    def to_dict(self, value, column):
        if value is None:
            return None
        vo = self.value_object_class.parse(value)
        return vo.to_primitive()

    def from_dict(self, value, column):
        if value is None:
            return None
        return self.value_object_class.parse(value)


class Email(String):
    data_type = 'string'
    data_format = 'email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, value, field=None):
        if not isinstance(value, str):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a string' % (
                                                str(field), str(value)
                                  ))
        return True


class Phone(String):
    data_type = 'string'
    data_format = r"\(?\+[0-9]{1,3}\)? ?-?[0-9]{1,3} ?-?[0-9]{3,5} ?-?[0-9]{4}( ?-?[0-9]{3})? ?(\w{1,10}\s?\d{1,6})?"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, value, field=None):
        if not isinstance(value, str):
            raise ValidationColumnException(
                self.schema_type, 'The value %s=%s is not a string' % (
                                                str(field), str(value)
                                  ))
        return True
