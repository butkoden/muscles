from muscles.core.schema import Model
from muscles.core.schema import Column
from muscles.core.schema import Key
from muscles.core.schema import FormParameter
from muscles.core.schema import HeaderParameter
from muscles.core.schema import QueryParameter
from muscles.core.schema import CookieParameter
from muscles.core.schema import PathParameter
from muscles.core.schema import File
from muscles.core.schema import String
from muscles.core.schema import Numeric
from muscles.core.schema import List
from muscles.core.schema import Enum


def test_FormParameter():
    """
    Проверяем схему параметров запроса FormParameter
    :return:
    """
    r = FormParameter('file', File, required=True, description='Path ID')
    assert r.dump() == {
        'required': True,
        'explode': False,
        'description': 'Path ID',
        'name': 'file',
        'schema': {
            'class': 'File',
            'children': [],
            'data_type': 'file',
            'type': 'string',
            'pattern': 'binary'
        },
        'in': 'formData'
    }
    r = FormParameter('file', File, required=False, description='Path ID')
    assert r.dump() == {
        'required': False,
        'explode': False,
        'description': 'Path ID',
        'name': 'file',
        'schema': {
            'class': 'File',
            'children': [],
            'data_type': 'file',
            'type': 'string',
            'pattern': 'binary'
        },
        'in': 'formData'
    }
    r = FormParameter('name', String, required=False, description='You Name')
    assert r.dump() == {
        'required': False,
        'explode': False,
        'description': 'You Name',
        'name': 'name',
        'schema': {
            'class': 'String',
            'children': [],
            'data_type': 'string',
            'type': 'string',
            'pattern': None,
            'length': 255
        },
        'in': 'formData'
    }


def test_HeaderParameter():
    """
    Проверяем схему параметров запроса FormParameter
    :return:
    """
    r = HeaderParameter('Header', Numeric, required=False, description='Header')
    assert r.dump() == {
        'required': False,
        'explode': False,
        'description': 'Header',
        'name': 'Header',
        'schema': {
            'class': 'Numeric',
            'children': [],
            'data_type': 'number',
            'type': 'number',
            'pattern': '^\\d+$',
            'precision': None,
            'scale': None,
            'decimal_return_scale': None,
            'asdecimal': True
        },
        'in': 'header'
    }


def test_CookieParameter():
    """
    Проверяем схему параметров запроса CookieParameter
    :return:
    """
    r = CookieParameter('csrftoken', String, required=False, description='Cookie')
    assert r.dump() == {
        'required': False,
        'explode': False,
        'description': 'Cookie',
        'name': 'csrftoken',
        'schema': {
            'class': 'String',
            'children': [],
            'data_type': 'string',
            'type': 'string',
            'pattern': None,
            'length': 255
        },
        'in': 'cookie'
    }


def test_PathParameter():
    """
    Проверяем схему параметров запроса FormParameter
    :return:
    """
    r = PathParameter('id', Numeric, required=True, description='Path ID')
    assert r.dump() == {
        'required': True,
        'explode': False,
        'description': 'Path ID',
        'name': 'id',
        'schema': {
            'class': 'Numeric',
            'children': [],
            'data_type': 'number',
            'type': 'number',
            'pattern': '^\\d+$',
            'precision': None,
            'scale': None,
            'decimal_return_scale': None,
            'asdecimal': True
        },
        'in': 'path'
    }


def test_QueryParameter():
    """
    Проверяем схему параметров запроса FormParameter
    :return:
    """
    r = QueryParameter('query1', List(Enum(enum=['one', 'two'])), required=False, description='Query1')
    assert r.dump() == {
        'required': False,
        'explode': False,
        'description': 'Query1',
        'name': 'query1',
        'schema': {
            'class': 'List',
            'children': [
                {
                    'class': 'Enum',
                    'children': [],
                    'data_type': 'enum',
                    'type': 'string',
                    'pattern': None,
                    'enum': ['one', 'two']
                }
            ],
            'data_type': 'array',
            'type': 'array',
            'pattern': None,
            'items': [
                {
                    'class': 'Enum',
                    'children': [],
                    'data_type': 'enum',
                    'type': 'string',
                    'pattern': None,
                    'enum': ['one', 'two']
                }
            ]
        },
        'in': 'query'
    }

    r = QueryParameter('query2', Enum(enum=['one', 'two']), required=False, description='Query2')
    assert r.dump() == {
        'required': False,
        'explode': False,
        'description': 'Query2',
        'name': 'query2',
        'schema': {
            'class': 'Enum',
            'children': [],
            'data_type': 'enum',
            'type': 'string',
            'pattern': None,
            'enum': ['one', 'two']
        },
        'in': 'query'
    }


