import re
from decimal import Decimal, InvalidOperation
from datetime import date, datetime, timezone
from urllib.parse import urlparse


class ValueObject:
    """
    Base immutable value object.

    Subclasses are expected to implement domain validation in `validate` and
    may override `normalize` to coerce input into canonical representation.
    """

    def __init__(self, value):
        normalized = self.normalize(value)
        self.validate(normalized)
        self._value = normalized

    @classmethod
    def parse(cls, value):
        if isinstance(value, cls):
            return value
        return cls(value)

    def normalize(self, value):
        return value

    def validate(self, value):
        return True

    @property
    def value(self):
        return self._value

    def to_primitive(self):
        return self._value

    def __str__(self):
        return str(self._value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._value!r})"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and other.value == self.value

    def __hash__(self):
        return hash((self.__class__, self.value))


class EmailValue(ValueObject):
    _pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def normalize(self, value):
        return str(value).strip().lower()

    def validate(self, value):
        if not isinstance(value, str) or not self._pattern.match(value):
            raise ValueError(f"Invalid email value: {value!r}")
        return True


class PhoneValue(ValueObject):
    _pattern = re.compile(r"^\+?[0-9\-\s\(\)]{7,20}$")

    def normalize(self, value):
        return str(value).strip()

    def validate(self, value):
        if not isinstance(value, str) or not self._pattern.match(value):
            raise ValueError(f"Invalid phone value: {value!r}")
        return True


class DateRangeValue(ValueObject):
    """
    Value format:
      {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'}
    """

    def normalize(self, value):
        if isinstance(value, DateRangeValue):
            return value.value
        if not isinstance(value, dict):
            raise ValueError("DateRangeValue expects dict with start/end")
        start = value.get("start")
        end = value.get("end")
        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()
        if isinstance(start, date):
            start = start.isoformat()
        if isinstance(end, date):
            end = end.isoformat()
        return {"start": start, "end": end}

    def validate(self, value):
        start = value.get("start")
        end = value.get("end")
        if not start or not end:
            raise ValueError("DateRangeValue requires start and end")
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
        except Exception as exc:
            raise ValueError(f"Invalid date range format: {exc}")
        if start_date > end_date:
            raise ValueError("DateRangeValue start must be <= end")
        return True


class NonEmptyStringValue(ValueObject):
    def normalize(self, value):
        return str(value).strip()

    def validate(self, value):
        if value == "":
            raise ValueError("String value must not be empty")
        return True


class SlugValue(ValueObject):
    _pattern = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def normalize(self, value):
        return str(value).strip().lower()

    def validate(self, value):
        if not self._pattern.match(value):
            raise ValueError(f"Invalid slug value: {value!r}")
        return True


class UrlValue(ValueObject):
    def normalize(self, value):
        return str(value).strip()

    def validate(self, value):
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ValueError(f"Invalid URL value: {value!r}")
        return True


class CountryCodeValue(ValueObject):
    _pattern = re.compile(r"^[A-Z]{2}$")

    def normalize(self, value):
        return str(value).strip().upper()

    def validate(self, value):
        if not self._pattern.match(value):
            raise ValueError(f"Invalid country code: {value!r}")
        return True


class PercentageValue(ValueObject):
    def normalize(self, value):
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid percentage value: {value!r}") from exc

    def validate(self, value):
        if value < Decimal("0") or value > Decimal("100"):
            raise ValueError("PercentageValue must be between 0 and 100")
        return True

    def to_primitive(self):
        return float(self.value)


class MoneyValue(ValueObject):
    _currency_pattern = re.compile(r"^[A-Z]{3}$")

    def normalize(self, value):
        if not isinstance(value, dict):
            raise ValueError("MoneyValue expects dict with amount/currency")
        amount = value.get("amount")
        currency = str(value.get("currency", "")).strip().upper()
        try:
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid money amount: {amount!r}") from exc
        return {"amount": decimal_amount, "currency": currency}

    def validate(self, value):
        if not self._currency_pattern.match(value["currency"]):
            raise ValueError("MoneyValue currency must be ISO-4217 alpha-3 code")
        return True

    def to_primitive(self):
        return {
            "amount": str(self.value["amount"]),
            "currency": self.value["currency"],
        }


class UtcDateTimeValue(ValueObject):
    def normalize(self, value):
        if isinstance(value, datetime):
            dt = value
        else:
            raw = str(value).strip()
            if raw.endswith("Z"):
                raw = raw[:-1] + "+00:00"
            dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            raise ValueError("UtcDateTimeValue requires timezone-aware datetime")
        return dt.astimezone(timezone.utc)

    def validate(self, value):
        if value.tzinfo is None:
            raise ValueError("UtcDateTimeValue requires timezone-aware datetime")
        return True

    def to_primitive(self):
        return self.value.isoformat().replace("+00:00", "Z")


class DateTimeRangeValue(ValueObject):
    """
    Value format:
      {'start': '<ISO datetime>', 'end': '<ISO datetime>'}
    """

    def normalize(self, value):
        if not isinstance(value, dict):
            raise ValueError("DateTimeRangeValue expects dict with start/end")
        start = UtcDateTimeValue.parse(value.get("start")).value
        end = UtcDateTimeValue.parse(value.get("end")).value
        return {"start": start, "end": end}

    def validate(self, value):
        if value["start"] > value["end"]:
            raise ValueError("DateTimeRangeValue start must be <= end")
        return True

    def to_primitive(self):
        return {
            "start": self.value["start"].isoformat().replace("+00:00", "Z"),
            "end": self.value["end"].isoformat().replace("+00:00", "Z"),
        }
