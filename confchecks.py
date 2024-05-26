"""
Various functions for checking configuration.
"""

import sys

try:
    from secrets import secrets
except ImportError:
    print(
        "WiFi credentials and configuration are kept in secrets.py, please add them there!"
    )
    raise


def bail(message):
    """
    Print message and exit with code 1.
    """
    print(message)
    sys.exit(1)


def check_string(name, mandatory=True):
    """
    Check is string with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, str):
        bail(f"not a string value for {name}: {value}")


def check_int(name, mandatory=True, min_val=None, max_val=None):
    """
    Check is integer with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, int):
        bail(f"not a integer value for {name}: {value}")

    if value < min_val or value > max_val:
        bail(f"{name} value not within {min_val},{max_val}: {value}")


def check_list(name, subtype, mandatory=True):
    """
    Check whether list with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, list):
        bail(f"not a integer value for {name}: {value}")

    for item in value:
        if item and not isinstance(item, subtype):
            bail(f"not a {subtype}: {item}")


def check_bytes(name, length, mandatory=True):
    """
    Check is bytes with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        bail(f"{name} is missing")

    if value and not isinstance(value, bytes):
        bail(f"not a byte value for {name}: {value}")

    if value and len(value) != length:
        bail(f"not correct length for {name}: {len(value)} should be {length}")
