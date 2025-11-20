"""
Various functions for checking configuration.
"""

import sys

# pylint: disable=unused-wildcard-import, wildcard-import
from names import *


class ConfCheckException(Exception):
    """
    designated exception for configuration check failure
    """


def check_string(secrets: dict, name: str, mandatory=True) -> None:
    """
    Check is string with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        raise ConfCheckException(f"{name} is missing")

    if value and not isinstance(value, str):
        raise ConfCheckException(f"not a string value for {name}: {value}")


def check_int(
    secrets: dict, name: str, mandatory=True, min_val=None, max_val=None
) -> None:
    """
    Check is integer with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        raise ConfCheckException(f"{name} is missing")

    if value is not None and not isinstance(value, int):
        raise ConfCheckException(f"not a integer value for {name}: {value}")

    if min_val is not None and value < min_val:
        raise ConfCheckException(f"{name} value {value} smaller than minimum {min_val}")

    if max_val is not None and value > max_val:
        raise ConfCheckException(f"{name} value {value} higher than maximum {max_val}")


def check_list(secrets: dict, name: str, subtype, mandatory=True) -> None:
    """
    Check whether list with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        raise ConfCheckException(f"{name} is missing")

    if value is None:
        raise ValueError(f"{name} should not be None")

    if value and not isinstance(value, list):
        raise ConfCheckException(f"not a integer value for {name}: {value}")

    for item in value:
        if item and not isinstance(item, subtype):
            raise ConfCheckException(f"not a {subtype}: {item}")


def check_bytes(secrets: dict, name: str, length: int, mandatory=True) -> None:
    """
    Check is bytes with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        raise ConfCheckException(f"{name} is missing")

    if value and not isinstance(value, bytes):
        raise ConfCheckException(f"not a byte value for {name}: {value}")

    if value and len(value) != length:
        raise ConfCheckException(
            f"not correct length for {name}: {len(value)} should be {length}"
        )


def bail(message: str) -> None:
    """
    Print message and exit with code 1.
    """
    print(message)
    sys.exit(1)


def check_tunables(secrets: dict) -> None:
    """
    Check that tunables are present and of correct type.
    Will exit the program on error.
    """
    check_string(secrets, LOG_LEVEL)

    # Even though different transport can be selected than Wi-Fi, the related tunables
    # are still mandatory, because at this point it is known which will be selected.
    check_string(secrets, SSID, mandatory=False)
    check_string(secrets, PASSWORD, mandatory=False)

    check_string(secrets, BROKER, mandatory=False)
    # MQTT topic is used for all transports so is mandatory.
    check_string(secrets, MQTT_TOPIC)
    check_string(secrets, LOG_TOPIC, mandatory=False)

    check_int(secrets, BROKER_PORT, min_val=0, max_val=65535, mandatory=False)

    check_int(secrets, DEEP_SLEEP_DURATION)
    check_int(secrets, SLEEP_DURATION_SHORT, mandatory=False)

    # Check consistency of the sleep values.
    sleep_default = secrets.get(DEEP_SLEEP_DURATION)
    sleep_short = secrets.get(SLEEP_DURATION_SHORT)
    if sleep_short is not None and sleep_short > sleep_default:
        bail(
            f"value of {SLEEP_DURATION_SHORT} bigger than value of {DEEP_SLEEP_DURATION}: "
            + f"{sleep_short} > {sleep_default}"
        )

    check_int(secrets, LIGHT_SLEEP_DURATION, mandatory=False)

    check_int(secrets, BATTERY_CAPACITY_THRESHOLD, mandatory=False)

    check_int(secrets, TX_POWER, mandatory=False)
    check_bytes(secrets, ENCRYPTION_KEY, 16, mandatory=False)

    check_int(secrets, LIGHT_GAIN, mandatory=False)
    light_gain = secrets.get(LIGHT_GAIN)
    if light_gain is not None and light_gain not in [1, 2]:
        bail(f"value of {LIGHT_GAIN} must be either 1 or 2")
