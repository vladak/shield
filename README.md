[![Python checks](https://github.com/vladak/shield/actions/workflows/python-checks.yml/badge.svg)](https://github.com/vladak/shield/actions/workflows/python-checks.yml)

# Shield

This repository contains code for ESP32 Adafruit Feather to measure temperature and send it to MQTT broker via WiFi.
The Feather is located outside on a balcony, running from a battery that is charged using a small solar panel.

This repository is called 'shield' as an allude to [Stevenson screen](https://en.wikipedia.org/wiki/Stevenson_screen) because
the Feather with the sensor is placed into a plastic screen, sometimes called "radiation shield": ![shield](/shield.jpg)

The cable running to the screen comes from a solar charger.

## Hardware

## Genesis

### Temperature sensor

Initially, [Adafruit ESP32-S2 Feather with BME280 Sensor](https://www.adafruit.com/product/5303) was used. 
This looked to be a fine all-in-one package, however initial experiments with temperature
readings using the built-in BME280 sensor showed that the skew of the metric due to the board being warmed up by 
the WiFi/SoC chip is too high - for ambient temperature of twenty/thirty-ish degrees of Celsius, the sensor
readings were forty-ish degrees of Celsius even though the code ran every couple of minutes to let the circuitry cool down.

Thus, I bought the [Adafruit TMP117 ±0.1°C High Accuracy I2C Temperature Sensor](https://www.adafruit.com/product/4821),
connected via STEMMA QT and this provides accurate temperature measurements.

### ESP32

XXX

### Solar charging

Initially, I used a small freebie solar charger with built-in batter that supplied power via USB cable. It was not enough to charge the ESP32, and likely the battery had very small capacity because it laid in the storage for couple of years.

XXX

## Configuration

### Prometheus MQTT exporter

The contents of `/etc/prometheus/mqtt-exporter.yaml` should look like this:

```yml
mqtt:
  # The MQTT broker to connect to
  server: tcp://localhost:1883
  # The Topic path to subscribe to. Be aware that you have to specify the wildcard.
  topic_path: devices/#
  # Optional: Regular expression to extract the device ID from the topic path. The default regular expression, assumes
  # that the last "element" of the topic_path is the device id.
  # The regular expression must contain a named capture group with the name deviceid
  # For example the expression for tasamota based sensors is "tele/(?P<deviceid>.*)/.*"
  device_id_regex: "(.*/)?(?P<deviceid>.*)"
  # The MQTT QoS level
  qos: 0
cache:
  # Timeout. Each received metric will be presented for this time if no update is send via MQTT.
  # Set the timeout to -1 to disable the deletion of metrics from the cache. The exporter presents the ingest timestamp
  # to prometheus.
  timeout: 60m
# This is a list of valid metrics. Only metrics listed here will be exported
metrics:
  -
    # The name of the metric in prometheus
    prom_name: temperature
    # The name of the metric in a MQTT JSON message
    mqtt_name: temperature
    # The prometheus help text for this metric
    help: temperature reading
    # The prometheus type for this metric. Valid values are: "gauge" and "counter"
    type: gauge
```

### Prometheus

Under the `scrape_configs` section in `/etc/prometheus/prometheus.yml` there should be:
```yml

  - job_name: mqtt
    # The MQTT based sensor publish the data only now and then.
    scrape_interval: 5m

    # If prometheus-mqtt-exporter is installed, grab metrics from external sensors.
    static_configs:
      - targets: ['localhost:9641']
```

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
