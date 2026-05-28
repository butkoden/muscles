from muscles.core.schema import Model
from muscles.core.schema import String
from muscles.core.schema import Column
from muscles.core.schema import Key
from muscles.core.schema import Collection


def test_Collection():
    """
    Проверяем схему Collection
    :return:
    """
    r = Collection("user",
                   Column("id", Key),
                   Column("name", String, index=True),
                   Column("family", String, index=True)
                   )
    assert r.dump() == {
        'class': 'Collection',
        'children': [
            {
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
                    'value': None,
                    'primary_key': False,
                    'example': None,
                    'error': None
                }
            },
            {
                'name': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255,
                    'index': True,
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
            },
            {
                'family': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255,
                    'index': True,
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
        ]
    }
