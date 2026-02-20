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
    expected_topic = "foo/bar"
    data = pack_data(expected_topic, None, None, None, None, None)
    mqtt_prefix, topic_unpacked, battery_level, co2_ppm, humidity, temperature, lux = (
        unpack_data(data)
    )
    assert mqtt_prefix.decode("ascii") == "MQTT:"
    mqtt_topic = topic_unpacked.decode("ascii")
    nul_idx = mqtt_topic.find("\x00")
    if nul_idx > 0:
        mqtt_topic = mqtt_topic[:nul_idx]
    assert mqtt_topic == expected_topic
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
