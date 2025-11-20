"""
Test sleep related functions.
"""

from unittest.mock import Mock

import pytest

# pylint: disable=unused-wildcard-import, wildcard-import
from names import *
from sleep import get_deep_sleep_duration


@pytest.mark.parametrize("above", [True, False])
def test_get_deep_sleep_duration(above: bool):
    """
    Test the get_deep_sleep_duration function to return short/long sleep duration
    for battery capacity above/below threshold, respectively.
    """
    secrets = {
        DEEP_SLEEP_DURATION: 42,
        SLEEP_DURATION_SHORT: 10,
        BATTERY_CAPACITY_THRESHOLD: 50,
    }
    battery_monitor = Mock()
    if above:
        battery_monitor.cell_percent = secrets[BATTERY_CAPACITY_THRESHOLD] + 1
        expected_duration = secrets[SLEEP_DURATION_SHORT]
    else:
        battery_monitor.cell_percent = secrets[BATTERY_CAPACITY_THRESHOLD]
        expected_duration = secrets[DEEP_SLEEP_DURATION]

    logger = Mock()
    assert (
        get_deep_sleep_duration(secrets, battery_monitor, logger) == expected_duration
    )
