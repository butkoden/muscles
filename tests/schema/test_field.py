from muscles.core.schema import Column
from muscles.core.schema import Boolean
from muscles.core.schema import Key
from muscles.core.schema import String
from muscles.core.schema import Enum
from muscles.core.schema import Email
from muscles.core.schema import DateTime
from muscles.core.schema import Float
from muscles.core.schema import List
from muscles.core.schema import Binary
from muscles.core.schema import UUID4
from muscles.core.schema import BigInteger
from muscles.core.schema import SmallInteger
from muscles.core.schema import Integer
from muscles.core.schema import Json
from muscles.core.schema import File
from muscles.core.schema import Date
from muscles.core.schema import Timestamp
from muscles.core.schema import Time
from muscles.core.schema import Text
from muscles.core.schema import Numeric
from muscles.core.schema import Phone


def test_Boolean():
    """
    Тест схемы поля Boolean
    :return:
    """
    c = Column("test", Boolean)
    assert c.dump() == {
        'test': {
            'class': 'Boolean',
            'children': [],
            'data_type': 'boolean',
            'type': 'boolean',
            'pattern': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_List():
    """
    Тест схемы поля List
    :return:
    """
    c = Column("test", List)
    assert c.dump() == {
        'test': {
            'class': 'List',
            'children': [],
            'data_type': 'array',
            'type': 'array',
            'pattern': None,
            'items': {},
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Float():
    """
    Тест схемы поля Float
    :return:
    """
    c = Column("test", Float)
    assert c.dump() == {
        'test': {
            'class': 'Float',
            'children': [],
            'data_type': 'float',
            'type': 'float',
            'pattern': None,
            'precision': None,
            'decimal_return_scale': None,
            'asdecimal': True,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Binary():
    """
    Тест схемы поля Binary
    :return:
    """
    c = Column("test", Binary)
    assert c.dump() == {
        'test': {
            'class': 'Binary',
            'children': [],
            'data_type': 'binary',
            'type': 'binary',
            'pattern': None,
            'length': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Enum():
    """
    Тест схемы поля Enum
    :return:
    """
    c = Column("test", Enum)
    assert c.dump() == {
        'test': {
            'class': 'Enum',
            'children': [],
            'data_type': 'enum',
            'type': 'string',
            'pattern': None,
            'enum': [],
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Key():
    """
    Тест схемы поля Key
    :return:
    """
    c = Column("test", Key)
    assert c.dump() == {
        'test': {
            'class': 'Key',
            'children': [],
            'data_type': 'key',
            'type': 'big_integer',
            'pattern': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_UUID4():
    """
    Тест схемы поля UUID4
    :return:
    """
    c = Column("test", UUID4)
    assert c.dump() == {
        'test': {
            'class': 'UUID4',
            'children': [],
            'data_type': 'uuid',
            'type': 'string',
            'pattern': '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[8-9a-fA-F][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$',
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_BigInteger():
    """
    Тест схемы поля BigInteger
    :return:
    """
    c = Column("test", BigInteger)
    assert c.dump() == {
        'test': {
            'class': 'BigInteger',
            'children': [],
            'data_type': 'big_integer',
            'type': 'big_integer',
            'pattern': None,
            'length': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_SmallInteger():
    """
    Тест схемы поля SmallInteger
    :return:
    """
    c = Column("test", SmallInteger)
    assert c.dump() == {
        'test': {
            'class': 'SmallInteger',
            'children': [],
            'data_type': 'small_integer',
            'type': 'small_integer',
            'pattern': None,
            'length': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Integer():
    """
    Тест схемы поля Integer
    :return:
    """
    c = Column("test", Integer)
    assert c.dump() == {
        'test': {
            'class': 'Integer',
            'children': [],
            'data_type': 'integer',
            'type': 'integer',
            'pattern': None,
            'length': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_String():
    """
    Тест схемы поля String
    :return:
    """
    c = Column("test", String)
    assert c.dump() == {
        'test': {
            'class': 'String',
            'children': [],
            'data_type': 'string',
            'type': 'string',
            'pattern': None,
            'length': 255,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Json():
    """
    Тест схемы поля Json
    :return:
    """
    c = Column("test", Json)
    assert c.dump() == {
        'test': {
            'class': 'Json',
            'children': [],
            'data_type': 'json',
            'type': 'json',
            'pattern': None,
            'length': 56000,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_File():
    """
    Тест схемы поля File
    :return:
    """
    c = Column("test", File)
    assert c.dump() == {
        'test': {
            'class': 'File',
            'children': [],
            'data_type': 'file',
            'type': 'string',
            'pattern': 'binary',
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Date():
    """
    Тест схемы поля Date
    :return:
    """
    c = Column("test", Date)
    assert c.dump() == {
        'test': {
            'class': 'Date',
            'children': [],
            'data_type': 'date',
            'type': 'date',
            'pattern': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_DateTime():
    """
    Тест схемы поля DateTime
    :return:
    """
    c = Column("test", DateTime)
    assert c.dump() == {
        'test': {
            'class': 'DateTime',
            'children': [],
            'data_type': 'date_time',
            'type': 'date_time',
            'pattern': None,
            'timezone': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Timestamp():
    """
    Тест схемы поля Timestamp
    :return:
    """
    c = Column("test", Timestamp)
    assert c.dump() == {
        'test': {
            'class': 'Timestamp',
            'children': [],
            'data_type': 'timestamp',
            'type': 'timestamp',
            'pattern': None,
            'timezone': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Time():
    """
    Тест схемы поля Time
    :return:
    """
    c = Column("test", Time)
    assert c.dump() == {
        'test': {
            'class': 'Time',
            'children': [],
            'data_type': 'time',
            'type': 'time',
            'pattern': None,
            'timezone': None,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Text():
    """
    Тест схемы поля Text
    :return:
    """
    c = Column("test", Text)
    assert c.dump() == {
        'test': {
            'class': 'Text',
            'children': [],
            'data_type': 'string',
            'type': 'string',
            'pattern': None,
            'length': 65535,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Numeric():
    """
    Тест схемы поля Numeric
    :return:
    """
    c = Column("test", Numeric)
    assert c.dump() == {
        'test': {
            'class': 'Numeric',
            'children': [],
            'data_type': 'number',
            'type': 'number',
            'pattern': '^\\d+$',
            'precision': None,
            'scale': None,
            'decimal_return_scale': None,
            'asdecimal': True,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Phone():
    """
    Тест схемы поля Phone
    :return:
    """
    c = Column("test", Phone)
    assert c.dump() == {
        'test': {
            'class': 'Phone',
            'children': [],
            'data_type': 'string',
            'type': 'string',
            'pattern': r"\(?\+[0-9]{1,3}\)? ?-?[0-9]{1,3} ?-?[0-9]{3,5} ?-?[0-9]{4}( ?-?[0-9]{3})? ?(\w{1,10}\s?\d{1,6})?",
            'length': 255,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }


def test_Email():
    """
    Тест схемы поля Email
    :return:
    """
    c = Column("test", Email)
    assert c.dump() == {
        'test': {
            'class': 'Email',
            'children': [],
            'data_type': 'string',
            'type': 'string',
            'pattern': 'email',
            'length': 255,
            'index': False,
            'unique': False,
            'default': None,
            'required': False,
            'title': None,
            'description': None,
            'nullable': True,
            'value': None,
            'primary_key': False,
            'example': None,
            'error': None
        }
    }





