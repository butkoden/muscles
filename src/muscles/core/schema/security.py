import base64
import hashlib
import hmac
import json
import time

from .schema import Schema
from .user import User


class BaseSecurity(Schema):

    schema = {}
    securitySchema = ""

    def __init__(self, *args, key=None, securitySchema=None, securityType=None, scope=None, **kwargs):
        self.securitySchema = securitySchema
        self.schema = {
            "type": securityType,
        }
        self.scope = scope or []
        self.key = key or securitySchema
        for key, val in kwargs.items():
            self.schema.update({key: val})
        kwargs["securitySchema"] = securitySchema
        kwargs["securityType"] = securityType
        super().__init__(*args, **kwargs)

    def dump(self) -> dict:
        return {self.key: self.schema}


class BasicAuthSecurity(BaseSecurity):
    securitySchema = "BasicAuth"

    def __init__(self, *args, key='Basic', securityType='http', scheme='basic', scope=None, **kwargs):
        self.scope = scope or []
        kwargs["key"] = key
        kwargs["securitySchema"] = self.securitySchema
        kwargs["type"] = securityType
        kwargs["scheme"] = scheme
        super().__init__(*args, **kwargs)


class ApiKeyAuthSecurity(BaseSecurity):
    securitySchema = "ApiKeyAuth"

    def __init__(self, *args, key='ApiKey', securityType='apiKey', location='header', name='X-Api-Token', scope=None,
                 **kwargs):
        self.scope = scope or []
        kwargs["securitySchema"] = self.securitySchema
        kwargs["key"] = key
        kwargs["type"] = securityType
        kwargs["in"] = location
        kwargs["name"] = name
        super().__init__(*args, **kwargs)


class BearerAuthSecurity(BaseSecurity):
    securitySchema = "BearerAuth"

    def __init__(self, *args, key='Bearer', securityType='http', scheme='bearer', scope=None, **kwargs):
        self.scope = scope or []
        kwargs["key"] = key
        kwargs["securitySchema"] = self.securitySchema
        kwargs["type"] = securityType
        kwargs["scheme"] = scheme
        super().__init__(*args, **kwargs)


class BearerJwtAuth(BearerAuthSecurity):
    def __init__(
        self,
        *args,
        secret: str,
        subject: str = "sub",
        algorithm: str = "HS256",
        ttl: int | None = None,
        **kwargs,
    ):
        self.secret = secret.encode("utf-8") if isinstance(secret, str) else secret
        self.subject = subject
        self.algorithm = algorithm
        self.ttl = ttl
        kwargs.setdefault("bearerFormat", "JWT")
        super().__init__(*args, **kwargs)

    @staticmethod
    def _b64encode(value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode((value + padding).encode("ascii"))

    def _sign(self, signing_input: str) -> str:
        if self.algorithm != "HS256":
            raise ValueError("Only HS256 JWT signing is supported")
        digest = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        return self._b64encode(digest)

    def issue(self, payload: dict, ttl: int | None = None) -> str:
        claims = dict(payload)
        expires_in = ttl if ttl is not None else self.ttl
        if expires_in is not None and "exp" not in claims:
            claims["exp"] = int(time.time()) + int(expires_in)
        header = {"alg": self.algorithm, "typ": "JWT"}
        signing_input = ".".join([
            self._b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            self._b64encode(json.dumps(claims, separators=(",", ":")).encode("utf-8")),
        ])
        return f"{signing_input}.{self._sign(signing_input)}"

    def decode(self, token: str) -> dict | None:
        try:
            header_b64, payload_b64, signature = token.split(".", 2)
            signing_input = f"{header_b64}.{payload_b64}"
            if not hmac.compare_digest(signature, self._sign(signing_input)):
                return None
            payload = json.loads(self._b64decode(payload_b64).decode("utf-8"))
            exp = payload.get("exp")
            if exp is not None and int(exp) < int(time.time()):
                return None
            return payload
        except Exception:
            return None

    def extract_token(self, authorization: str | None) -> str | None:
        if not authorization:
            return None
        parts = authorization.strip().split()
        while parts and parts[0].lower() == "bearer":
            parts = parts[1:]
        if len(parts) != 1:
            return None
        return parts[0]

    def authenticate_header(self, authorization: str | None) -> dict | None:
        token = self.extract_token(authorization)
        if not token:
            return None
        payload = self.decode(token)
        if payload is None:
            return None
        user = User(token=token, name=payload.get("name") or payload.get(self.subject), rules=payload)
        user.uid = payload.get(self.subject)
        return {
            "payload": payload,
            "token": token,
            "user": user,
        }
