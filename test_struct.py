"""
test structure packing
"""

import pytest

from data import pack_data


def test_pack():
    """
    call the pack_data() to ensure it packs the data into less than 60 bytes
    """
    data = pack_data("foo/bar", 80, 1200, 33, 21, 4000)
    assert len(data) <= 60


def test_mqtt_topic_length_max():
    """
    call the pack_data() to ensure it does not throw an exception
    """
    with pytest.raises(ValueError):
        pack_data("devices/foo/bar/foo/bar/foo/bar/foo", 80, 1200, 33, 21, 4000)
