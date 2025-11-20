"""
Test sleep related functions.
"""

from unittest.mock import Mock

import pytest

# pylint: disable=unused-wildcard-import, wildcard-import
from names import *
from sleep import get_deep_sleep_duration


@pytest.mark.parametrize(
    "above,is_battery", [(True, True), (True, False), (False, True), (False, False)]
)
def test_get_deep_sleep_duration(above: bool, is_battery: bool):
    """
    Test the get_deep_sleep_duration function to return short/long sleep duration
    for battery capacity above/below threshold, respectively.
    If there is no battery monitor, the sleep duration should be always
    of the long sleep duration.
    """
    secrets = {
        DEEP_SLEEP_DURATION: 42,
        SLEEP_DURATION_SHORT: 10,
        BATTERY_CAPACITY_THRESHOLD: 50,
    }
    battery_monitor = None
    if is_battery:
        battery_monitor = Mock()
        if above:
            battery_monitor.cell_percent = secrets[BATTERY_CAPACITY_THRESHOLD] + 1
            expected_duration = secrets[SLEEP_DURATION_SHORT]
        else:
            battery_monitor.cell_percent = secrets[BATTERY_CAPACITY_THRESHOLD]
            expected_duration = secrets[DEEP_SLEEP_DURATION]
    else:
        expected_duration = secrets[DEEP_SLEEP_DURATION]

    logger = Mock()
    assert (
        get_deep_sleep_duration(secrets, battery_monitor, logger) == expected_duration
    )
