from muscles.core.schema import Model
from muscles.core.schema import Column
from muscles.core.schema import Key
from muscles.core.schema import ResponseBody
from muscles.core.schema import HtmlResponseBody
from muscles.core.schema import JsonResponseBody
from muscles.core.schema import XmlResponseBody
from muscles.core.schema import TextResponseBody


def test_ResponseBody():
    """
    Проверяем схему ответа ResponseBody
    :return:
    """
    r = ResponseBody(description='OK', content_type='application/pdf')
    assert r.dump() == {
        'application/pdf': {
            'http_code': None,
            'content_type': 'application/pdf',
            'description': 'OK',
            'schema': None
        }
    }


def test_HtmlResponseBody():
    """
    Проверяем схему ответа HtmlResponseBody
    :return:
    """
    r = HtmlResponseBody(description='OK')
    assert r.dump() == {
        'text/html': {
            'http_code': None,
            'content_type': 'text/html',
            'description': 'OK',
            'schema': None
        }
    }


def test_XmlResponseBody():
    """
    Проверяем схему ответа XmlResponseBody
    :return:
    """
    r = XmlResponseBody(description='WARNING')
    assert r.dump() == {
        'application/xml': {
            'http_code': None,
            'content_type': 'application/xml',
            'description': 'WARNING',
            'schema': None
        }
    }


def test_JsonResponseBody():
    """
    Проверяем схему ответа JsonResponseBody
    :return:
    """

    class SchTest(Model):
        id = Column(Key)

    r = JsonResponseBody(model=SchTest)
    assert r.dump() == {
        'application/json': {
            'http_code': None,
            'content_type': 'application/json',
            'description': None,
            'schema': {
                '$ref': '#/components/schemas/SchTest'
            }
        }
    }



def test_TextResponseBody():
    """
    Проверяем схему ответа TextResponseBody
    :return:
    """
    r = TextResponseBody()
    assert r.dump() == {
        'text/plain': {
            'http_code': None,
            'content_type': 'text/plain',
            'description': None,
            'schema': None
        }
    }


def test_TextResponseBody_with_model():
    """
    Проверяем схему ответа TextResponseBody с указанием модели и http кодом ответа
    :return:
    """
    class SchTest(Model):
        id = Column(Key)

    r = TextResponseBody(http_code=200, model=SchTest)
    assert r.dump() == {
        'text/plain': {
            'http_code': 200,
            'content_type': 'text/plain',
            'description': None,
            'schema': {
                '$ref': '#/components/schemas/SchTest'
            }
        }
    }




