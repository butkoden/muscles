from muscles.core.schema import Column
from muscles.core.schema import DateRangeValue
from muscles.core.schema import PhoneValue
from muscles.core.schema import Model
from muscles.core.schema import ValueObject
from muscles.core.schema import ValueObjectField


class EmailAddress(ValueObject):
    def normalize(self, value):
        return str(value).strip().lower()

    def validate(self, value):
        if "@" not in value:
            raise ValueError("email must contain @")
        return True


class Contact(Model):
    email = Column(ValueObjectField(value_object_class=EmailAddress))


def test_value_object_equality():
    left = EmailAddress("User@Example.COM ")
    right = EmailAddress("user@example.com")
    assert left == right
    assert left.to_primitive() == "user@example.com"


def test_value_object_field_in_model():
    contact = Contact(email="User@Example.COM ")
    assert isinstance(contact.email, EmailAddress)
    assert contact.email.to_primitive() == "user@example.com"
    assert contact.as_dict()["email"] == "user@example.com"


def test_value_object_field_rejects_invalid_value():
    try:
        Contact(email="invalid")
    except Exception as exc:
        assert "email must contain @" in str(exc)
    else:
        raise AssertionError("Expected invalid value to raise error")


def test_phone_value():
    phone = PhoneValue("+1 (202) 555-0101")
    assert phone.to_primitive() == "+1 (202) 555-0101"
    try:
        PhoneValue("invalid-phone")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid phone to raise ValueError")


def test_date_range_value():
    range_value = DateRangeValue({"start": "2026-01-01", "end": "2026-01-31"})
    assert range_value.to_primitive() == {"start": "2026-01-01", "end": "2026-01-31"}

    try:
        DateRangeValue({"start": "2026-02-01", "end": "2026-01-01"})
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid date range ordering to fail")
