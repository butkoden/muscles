import copy
import uuid
from abc import abstractmethod
from muscles.core.core import ApplicationMeta
from muscles.core.core import Dependency
from muscles.core.schema import Model
from muscles.core.schema import Column
from muscles.core.schema import UUID4
from muscles.core.schema import Key
from muscles.core.schema import String
from muscles.core.schema import Enum
from muscles.core.schema import Date
from muscles.core.schema import DateTime
from muscles.core.schema import FormRequestBody
from muscles.core.schema import ValidationColumnException


class SchTest(Model):
    id = Column(Key)
    
    
class User(Model):
    id = Column(UUID4, primary_key=True, default='gen')
    name = Column(String, index=True, default="John")
    email = Column(String, index=True)
    status = Column(Enum(enum=['inactive', 'deleted', 'blocked', 'active']), index=True)
    birthday = Column(Date)
    created_at = Column(DateTime)


class UtilInterface:
    @abstractmethod
    def test(self):
        return "Active 0"


class Util(UtilInterface):
        def test(self):
            return "Active 1"
        

class App(metaclass=ApplicationMeta):
    util = Dependency(UtilInterface, Util)


column_name_User = {
    'name': {
        'class': 'String',
        'children': [],
        'data_type': 'string',
        'type': 'string',
        'pattern': None,
        'length': 255,
        'index': True,
        'unique': False,
        'default': "John",
        'required': False,
        'title': None,
        'description': None,
        'nullable': True,
        'value': 'test name',
        'primary_key': False,
        'example': None,
        'error': None
    }
}


column_id_SchTest = {
    'SchTest': {
        'type': 'object',
        'properties': {
            'id': {
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
                'value': 'id',
                'primary_key': False,
                'example': None,
                'error': None
            }
        }
    }
}


def test_zero():
    """
    Проверяем работоспособность схемы
    :return:
    """
    u = SchTest(id="id")
    assert u.dump() == column_id_SchTest


def test_model():
    """
    Модели схемы
    :return:
    """
    u = User(name="test name", status="blocked")
    u.email = 'mmm@mail.ru'
    assert u.columns["name"].value == "test name"
    assert u.status == "blocked"
    assert u.columns["name"].dump() == column_name_User


def test_model_validate():
    """
    Модели схемы
    :return:
    """
    try:
        u = User(status="none")
    except ValidationColumnException as vce:
        assert isinstance(vce, ValidationColumnException)
        assert vce.message == 'The value status=none does not match any of the possible values'
    u = User(status="blocked")
    u.email = 'mmm@mail.ru'

    col_name = copy.deepcopy(column_name_User)
    col_name['name']['value'] = 'John'

    assert isinstance(u.columns["id"].value, uuid.UUID)
    assert u.columns["name"].value == "John"
    assert u.status == "blocked"
    assert u.columns["name"].dump() == col_name


def test_request():
    """
    Схемы запросов
    :return:
    """
    u = User(name="test name", status="blocked")
    u.email = 'mmm@mail.ru'

    r = FormRequestBody(model=u)

    assert r.content_type == 'application/x-www-form-urlencoded'
    assert r.model.columns["name"].dump() == column_name_User





