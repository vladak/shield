"""
conftest tests
"""

import pytest

import confchecks


class FakeBailException(Exception):
    """
    designated exception for overriding confchecks.bail()
    """


@pytest.fixture
def fake_bail():
    """
    override confchecks.bail() with a function that raises FakeBailException
    """

    # pylint: disable=redefined-outer-name
    def fake_bail(message):
        raise FakeBailException(message)

    confchecks.bail = fake_bail


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_missing(fake_bail):
    """
    Test the case of missing name to check.
    """
    with pytest.raises(FakeBailException):
        confchecks.check_int({"foo": 60}, "nonexistent")


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_missing_optional():
    """
    Test the case of missing optional name.
    """
    confchecks.check_int({"foo": 60}, "nonexistent", mandatory=False)


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_invalid_value_type(fake_bail):
    """
    Test the case of invalid value type.
    """
    with pytest.raises(FakeBailException):
        confchecks.check_int({"foo": "bar"}, "foo")


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_min_unspecified_positive():
    """
    Test the case of unspecified min.
    """
    confchecks.check_int({"foo": 42}, "foo", max_val=60)


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_max_unspecified_positive():
    """
    Test the case of unspecified max.
    """
    confchecks.check_int({"foo": 42}, "foo", min_val=10)


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_max_negative(fake_bail):
    """
    Test the case of value higher than max.
    """
    with pytest.raises(FakeBailException):
        confchecks.check_int({"foo": 42}, "foo", max_val=10)


# pylint: disable=unused-argument, redefined-outer-name
def test_check_int_min_negative(fake_bail):
    """
    Test the case of value lower than min.
    """
    with pytest.raises(FakeBailException):
        confchecks.check_int({"foo": 42}, "foo", min_val=50)
