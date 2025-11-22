"""
conftest tests
"""

import pytest

from confchecks import ConfCheckException, check_int, check_string


def test_check_int_missing():
    """
    Test the case of missing name to check.
    """
    with pytest.raises(ConfCheckException):
        check_int({"foo": 60}, "nonexistent")


def test_check_int_missing_optional():
    """
    Test the case of missing optional name.
    """
    check_int({"foo": 60}, "nonexistent", mandatory=False)


def test_check_int_invalid_value_type():
    """
    Test the case of invalid value type.
    """
    with pytest.raises(ConfCheckException):
        check_int({"foo": "bar"}, "foo")


def test_check_int_min_unspecified_positive():
    """
    Test the case of unspecified min.
    """
    check_int({"foo": 42}, "foo", max_val=60)


def test_check_int_max_unspecified_positive():
    """
    Test the case of unspecified max.
    """
    check_int({"foo": 42}, "foo", min_val=10)


def test_check_int_max_negative():
    """
    Test the case of value higher than max.
    """
    with pytest.raises(ConfCheckException):
        check_int({"foo": 42}, "foo", max_val=10)


def test_check_int_min_negative():
    """
    Test the case of value lower than min.
    """
    with pytest.raises(ConfCheckException):
        check_int({"foo": 42}, "foo", min_val=50)


def test_check_string_missing():
    """
    Test the case of missing name to check.
    """
    with pytest.raises(ConfCheckException):
        check_string({"foo": "bar"}, "nonexistent")


def test_check_string_missing_optional():
    """
    Test the case of missing optional name.
    """
    check_string({"foo": "bar"}, "nonexistent", mandatory=False)


def test_check_string_invalid_value_type():
    """
    Test the case of invalid value type.
    """
    with pytest.raises(ConfCheckException):
        check_string({"foo": 42}, "foo")
