import re
from datetime import date, datetime


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
