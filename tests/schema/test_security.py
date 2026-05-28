from muscles.core.schema import Model
from muscles.core.schema import Column
from muscles.core.schema import Key
from muscles.core.schema import BasicAuthSecurity
from muscles.core.schema import ApiKeyAuthSecurity
from muscles.core.schema import BearerAuthSecurity


def test_BasicAuthSecurity():
    """
    Проверяем схему BasicAuthSecurity
    :return:
    """
    r = BasicAuthSecurity()
    assert r.dump() == {'Basic': {'type': 'http', 'scheme': 'basic'}}


def test_ApiKeyAuthSecurity():
    """
    Проверяем схему ApiKeyAuthSecurity
    :return:
    """
    r = ApiKeyAuthSecurity()
    assert r.dump() == {
        'ApiKey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Api-Token'
        }
    }


def test_BearerAuthSecurity():
    """
    Проверяем схему BearerAuthSecurity
    :return:
    """
    r = BearerAuthSecurity()
    assert r.dump() == {
        'Bearer': {
            'type': 'http',
            'scheme': 'basic'
        }
    }


