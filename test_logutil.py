"""
test logging utilities
"""

import adafruit_logging as logging
import pytest

from logutil import get_log_level


def test_get_log_level_attr_invalid():
    """
    invalid level name should raise exception
    """
    with pytest.raises(AttributeError):
        get_log_level("foo")


def test_get_log_level_attr():
    """
    log level as string
    """
    # pylint: disable=no-member
    assert get_log_level("INFO") == logging.INFO


def test_get_log_level_default():
    """
    default log level
    """
    # pylint: disable=no-member
    assert get_log_level(None) == logging.INFO


def test_get_log_level_int():
    """
    log level as int
    """
    # pylint: disable=no-member
    assert get_log_level(20) == logging.INFO


def test_get_log_level_int_as_str():
    """
    log level as int in string format
    """
    # pylint: disable=no-member
    assert get_log_level("20") == logging.INFO
