"""
Various functions for checking configuration.
"""


class ConfCheckException(Exception):
    """
    designated exception for configuration check failure
    """


def check_string(secrets, name, mandatory=True):
    """
    Check is string with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        raise ConfCheckException(f"{name} is missing")

    if value and not isinstance(value, str):
        raise ConfCheckException(f"not a string value for {name}: {value}")


def check_int(secrets, name, mandatory=True, min_val=None, max_val=None):
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


def check_list(secrets, name, subtype, mandatory=True):
    """
    Check whether list with given name is present in secrets.
    """
    value = secrets.get(name)
    if value is None and mandatory:
        raise ConfCheckException(f"{name} is missing")

    if value and not isinstance(value, list):
        raise ConfCheckException(f"not a integer value for {name}: {value}")

    for item in value:
        if item and not isinstance(item, subtype):
            raise ConfCheckException(f"not a {subtype}: {item}")


def check_bytes(secrets, name, length, mandatory=True):
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
