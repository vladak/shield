"""
test structure packing
"""

import math

import pytest

from data import pack_data, unpack_data


def test_pack():
    """
    call the pack_data() to ensure it packs the data into less than 60 bytes
    """
    data = pack_data("foo/bar", 80, 1200, 33, 21, 4000)
    assert len(data) <= 60


def test_pack_none():
    """
    call the pack_data() to ensure it packs the None values as float('nan')
    or -1 in case of float and integer, respectively.
    """
    topic = "foo/bar"
    data = pack_data(topic, None, None, None, None, None)
    mqtt_prefix, topic_unpacked, battery_level, co2_ppm, humidity, temperature, lux = (
        unpack_data(data)
    )
    assert mqtt_prefix == "MQTT:"
    assert topic_unpacked == topic
    assert math.isnan(battery_level)
    assert co2_ppm == 0
    assert math.isnan(humidity)
    assert math.isnan(temperature)
    assert math.isnan(lux)


def test_mqtt_topic_length_max():
    """
    Call the pack_data() to ensure it throws the ValueError exception on
    too long MQTT topic.
    """
    with pytest.raises(ValueError):
        pack_data("devices/foo/bar/foo/bar/foo/bar/foo", 80, 1200, 33, 21, 4000)
