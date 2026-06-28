from muscles.core.schema import Model
from muscles.core.schema import Column
from muscles.core.schema import Key
from muscles.core.schema import BasicAuthSecurity
from muscles.core.schema import ApiKeyAuthSecurity
from muscles.core.schema import BearerAuthSecurity
from muscles.core.schema import BearerJwtAuth


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
            'scheme': 'bearer'
        }
    }


def test_BearerJwtAuth_issue_and_authenticate():
    auth = BearerJwtAuth(secret="secret", subject="sub")
    token = auth.issue({"sub": "user-1", "name": "Denis"})

    result = auth.authenticate_header(f"Bearer Bearer {token}")

    assert result["payload"]["sub"] == "user-1"
    assert result["user"].token == token
    assert str(result["user"].uuid)


def test_BearerJwtAuth_rejects_invalid_token():
    auth = BearerJwtAuth(secret="secret")

    assert auth.extract_token("Basic x") is None
    assert auth.authenticate_header("Bearer invalid") is None
