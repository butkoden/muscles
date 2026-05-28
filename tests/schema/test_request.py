from muscles.core.schema import Model
from muscles.core.schema import Column
from muscles.core.schema import Key
from muscles.core.schema import JsonRequestBody
from muscles.core.schema import MultipartRequestBody
from muscles.core.schema import XmlRequestBody
from muscles.core.schema import TextRequestBody
from muscles.core.schema import PayloadRequestBody
from muscles.core.schema import FileRequestBody
from muscles.core.schema import FormRequestBody
from muscles.core.schema import File
from muscles.core.schema import String
from muscles.core.schema import Numeric
from muscles.core.schema import List
from muscles.core.schema import Enum


def test_JsonRequestBody():
    """
    Проверяем схему тела запроса JsonRequestBody
    :return:
    """
    r = JsonRequestBody(description='Json', model=File)
    assert r.dump() == {
        'application/json': {
            'description': 'Json',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = JsonRequestBody(description='Json', model=String, is_list=True)
    assert r.dump() == {
        'application/json': {
            'description': 'Json',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }

    r = JsonRequestBody(description='Json', model=String, is_list=True, max_items=10, min_items=1)
    assert r.dump() == {
        'application/json': {
            'description': 'Json',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                },
                'minItems': 1,
                'maxItems': 10
            }
        }
    }

    r = JsonRequestBody(description='Json', model=String, is_list=True, unique_items=True)
    assert r.dump() == {
        'application/json': {
            'description': 'Json',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                },
                'uniqueItems': True
            }
        }
    }


def test_MultipartRequestBody():
    """
    Проверяем схему тела запроса MultipartRequestBody
    :return:
    """
    r = MultipartRequestBody(description='Form', model=File)
    assert r.dump() == {
        'multipart/form-data': {
            'description': 'Form',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = MultipartRequestBody(description='Form', model=String, is_list=True)
    assert r.dump() == {
        'multipart/form-data': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }

    r = MultipartRequestBody(description='Form', model=String, is_list=True, max_items=10, min_items=1)
    assert r.dump() == {
        'multipart/form-data': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                },
                'minItems': 1,
                'maxItems': 10
            }
        }
    }

    r = MultipartRequestBody(description='Form', model=String, is_list=True, unique_items=True)
    assert r.dump() == {
        'multipart/form-data': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                },
                'uniqueItems': True
            }
        }
    }


def test_XmlRequestBody():
    """
    Проверяем схему тела запроса XmlRequestBody
    :return:
    """
    r = XmlRequestBody(description='Form', model=File)
    assert r.dump() == {
        'application/xml': {
            'description': 'Form',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = XmlRequestBody(description='Form', model=String, is_list=True)
    assert r.dump() == {
        'application/xml': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }


def test_TextRequestBody():
    """
    Проверяем схему тела запроса TextRequestBody
    :return:
    """
    r = TextRequestBody(description='Form', model=File)
    assert r.dump() == {
        'text/plain': {
            'description': 'Form',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = TextRequestBody(description='Form', model=String, is_list=True)
    assert r.dump() == {
        'text/plain': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }


def test_PayloadRequestBody():
    """
    Проверяем схему тела запроса PayloadRequestBody
    :return:
    """
    r = PayloadRequestBody(description='Form', model=File)
    assert r.dump() == {
        'text/plain': {
            'description': 'Form',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = PayloadRequestBody(description='Form', model=String, is_list=True)
    assert r.dump() == {
        'text/plain': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }


def test_FileRequestBody():
    """
    Проверяем схему тела запроса FileRequestBody
    :return:
    """
    r = FileRequestBody(content_type="image/png", description='Form', model=File)
    assert r.dump() == {
        'image/png': {
            'description': 'Form',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = FileRequestBody(content_type="image/png", description='Form', model=String, is_list=True)
    assert r.dump() == {
        'image/png': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }


def test_FormRequestBody():
    """
    Проверяем схему тела запроса FormRequestBody
    :return:
    """
    r = FormRequestBody(content_type="image/png", description='Form', model=File)
    assert r.dump() == {
        'application/x-www-form-urlencoded': {
            'description': 'Form',
            'schema': {
                'class': 'File',
                'children': [],
                'data_type': 'file',
                'type': 'string',
                'pattern': 'binary'
            }
        }
    }

    r = FormRequestBody(content_type="image/png", description='Form', model=String, is_list=True)
    assert r.dump() == {
        'application/x-www-form-urlencoded': {
            'description': 'Form',
            'schema': {
                'type': 'array',
                'items': {
                    'class': 'String',
                    'children': [],
                    'data_type': 'string',
                    'type': 'string',
                    'pattern': None,
                    'length': 255
                }
            }
        }
    }

