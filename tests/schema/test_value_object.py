from muscles.core.schema import Column
from muscles.core.schema import CountryCodeValue
from muscles.core.schema import DateTimeRangeValue
from muscles.core.schema import DateRangeValue
from muscles.core.schema import MoneyValue
from muscles.core.schema import NonEmptyStringValue
from muscles.core.schema import PercentageValue
from muscles.core.schema import PhoneValue
from muscles.core.schema import SlugValue
from muscles.core.schema import UrlValue
from muscles.core.schema import UtcDateTimeValue
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


def test_non_empty_string_value():
    item = NonEmptyStringValue("  hello  ")
    assert item.to_primitive() == "hello"
    try:
        NonEmptyStringValue("   ")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected empty string to fail")


def test_slug_value():
    slug = SlugValue("Hello-world-2026")
    assert slug.to_primitive() == "hello-world-2026"
    try:
        SlugValue("bad slug")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected bad slug to fail")


def test_url_value():
    url = UrlValue("https://butko.info/resume")
    assert url.to_primitive() == "https://butko.info/resume"
    try:
        UrlValue("ftp://butko.info")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected non-http scheme to fail")


def test_country_code_value():
    cc = CountryCodeValue("ru")
    assert cc.to_primitive() == "RU"
    try:
        CountryCodeValue("RUS")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected non-alpha2 country code to fail")


def test_percentage_value():
    pct = PercentageValue("99.9")
    assert pct.to_primitive() == 99.9
    try:
        PercentageValue(200)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected out-of-range percentage to fail")


def test_money_value():
    money = MoneyValue({"amount": "123.45", "currency": "usd"})
    assert money.to_primitive() == {"amount": "123.45", "currency": "USD"}
    try:
        MoneyValue({"amount": "abc", "currency": "USD"})
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid amount to fail")


def test_utc_datetime_value():
    dt = UtcDateTimeValue("2026-06-01T10:00:00+03:00")
    assert dt.to_primitive().endswith("Z")
    try:
        UtcDateTimeValue("2026-06-01T10:00:00")
    except ValueError:
        pass
    else:
        raise AssertionError("Expected naive datetime to fail")


def test_datetime_range_value():
    window = DateTimeRangeValue({
        "start": "2026-06-01T10:00:00+03:00",
        "end": "2026-06-01T10:30:00+03:00",
    })
    primitive = window.to_primitive()
    assert primitive["start"].endswith("Z")
    assert primitive["end"].endswith("Z")
    try:
        DateTimeRangeValue({
            "start": "2026-06-01T10:30:00+03:00",
            "end": "2026-06-01T10:00:00+03:00",
        })
    except ValueError:
        pass
    else:
        raise AssertionError("Expected reversed datetime range to fail")
