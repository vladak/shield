[![Python checks](https://github.com/vladak/shield/actions/workflows/python-checks.yml/badge.svg)](https://github.com/vladak/shield/actions/workflows/python-checks.yml)

# Shield

code for ESP32 Adafruit Feather to measure temperature and send it to MQTT broker

This is used specifically on [Adafruit ESP32-S2 Feather with BME280 Sensor](https://www.adafruit.com/product/5303). 
This looked to be a fine all-in-one package, however initial experiments with temperature
readings using the built-in BME280 sensor showed that the skew of the metric due to the board being warmed up by 
the WiFi/SoC chip is too high - for ambient temperature of twenty/thirty-ish degrees of Celsius, the sensor
readings were forty-ish degrees of Celsius even though the code ran every couple of minutes to let the circuitry cool down.

Thus, I bought the [Adafruit TMP117 ±0.1°C High Accuracy I2C Temperature Sensor](https://www.adafruit.com/product/4821),
connected via STEMMA QT and this provides accurate temperature measurements.

This repository is called 'shield' as an allude to [Stevenson screen](https://en.wikipedia.org/wiki/Stevenson_screen) because
the Feather with the sensor is placed into a plastic screen, sometimes called "radiation shield": ![shield](/shield.jpg)

The cable running to the screen comes from a solar charger.

## Usage

There needs to be a `secrets.py` file that contains Wi-Fi credentials and information about the MQTT broker.
It can look like this:
```python
# This file is where you keep secret settings, passwords, and tokens!
# If you put them in the code you risk committing that info or sharing it

secrets = {
    "ssid": "foo",
    "password": "bar",
    "broker": "172.40.0.3",
    "broker_port": 1883,
    "mqtt_topic": "devices/terasa/shield",
    "sleep_duration": 300,
    "log_level": "INFO",
}
```

To load this onto the Feather, I recommend using the [Mu editor](https://codewith.mu/).
