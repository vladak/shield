[![Python checks](https://github.com/vladak/shield/actions/workflows/python-checks.yml/badge.svg)](https://github.com/vladak/shield/actions/workflows/python-checks.yml)

# Shield

This repository contains code for ESP32 Adafruit Feather to measure temperature and send it to MQTT broker via WiFi.
The Feather is located outside on a balcony, running from a battery that is charged using a small solar panel.

This repository is called 'shield' as an allude to [Stevenson screen](https://en.wikipedia.org/wiki/Stevenson_screen) because
the Feather with the cicuitry is placed into a plastic screen, sometimes called "radiation shield": 

<img src="shield.jpg" alt="drawing" width="400"/>

The cable running to the screen comes from the solar panel.

All in all, that's a lot of trouble and materials to get a simple temperature measurement from the outside.
However, I used that as a way to learn more about solar charging, CircuitPython, microcontrollers, electronics etc. and I mostly enjoyed the process of building it.

## Hardware

Here is a bill of materials:

Purpose | Name
---|---
microcontroller | [ESP32 Feather V2 with w.FL antenna connector](https://www.adafruit.com/product/5438)
antenna | [WiFi Antenna with w.FL / MHF3 / IPEX3 Connector](https://www.adafruit.com/product/5445)
battery | [2000 mAh from Pimoroni](https://shop.pimoroni.com/products/lipo-battery-pack?variant=20429082247)
solar charger | [Adafruit Universal USB / DC / Solar Lithium Ion/Polymer charger - bq24074](https://www.adafruit.com/product/4755)
jack adapter for solar charger | [3.5mm / 1.1mm to 5.5mm / 2.1mm DC Jack Adapter](https://www.adafruit.com/product/4287)
solar panel | [6V 2W Solar Panel - ETFE - Voltaic P126](https://www.adafruit.com/product/5366)
extension cable | [2.1mm female/male barrel jack extension cable - 1.5m](https://www.adafruit.com/product/327)
battery gauge | [Adafruit MAX17048 LiPoly / LiIon Fuel Gauge and Battery Monitor - STEMMA JST PH](https://www.adafruit.com/product/5580)
thermistor | [Ultra Thin 10K Thermistor - B3950 NTC](https://www.adafruit.com/product/4890)
power jumper cables | [JST-PH 2-pin Jumper Cable - 100mm long](https://www.adafruit.com/product/4714)
temperature sensor | [Adafruit TMP117 ±0.1°C High Accuracy I2C Temperature Sensor - STEMMA QT](https://www.adafruit.com/product/4821)

Most of the stuff comes from [Adafruit](https://www.adafruit.com/).

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

After I put the code together to read the sensor data and send it to MQTT broker via WiFi, I bumped into [troubles with MQTT communication being stuck](https://forums.adafruit.com/viewtopic.php?t=193414). The MQTT library was merely a victim of some underlying firmware/network problem. I [solved the MQTT part](https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/pull/117) which helped to avoid the stuck program, however did not help with getting the data to the local MQTT broker. The program running on the ESP32 was set to read the sensor data, publish them to MQTT broker and enter deep sleep for 5 minutes to conserve battery power. For a number of these 5 minute intervals, it did not manage to send the data successfully.

I suspected this is caused by some networking problem. Even though the ESP32 was located some 3 meters away from the WiFi access point and the MQTT broker was connected via Ethernet switched network to the AP, the communication was still not stable. So, a ESP32 that would be capable of running CircuitPython, had STEMMA QT and external antenna connector was needed. Luckily, I found [ESP32 Feather V2 with w.FL antenna connector](https://www.adafruit.com/product/5438). After I went through the hoops of installing CircuitPython on it (this ESP32 does not have built-in USB capabilities, so requires different workflow in order to upload files to its flash), and running initial tests, it is evident that the networking communication is way better - it no longer takes a significant latency to connect to WiFi (involves ARP, DHCP etc.).

### Solar charging

Initially, I used a small freebie solar charger with built-in battery that supplied power via USB cable. It was not enough to charge the ESP32, and likely the battery had very small capacity because it laid in the storage for couple of years.

I wanted to monitor the capacity of the battery. In practice, that this metric will be published as MQTT message and eventually consumed by Grafana. This way, Grafana can provide alerting if the capacity drops too low. Since the [Adafruit bq24074 charger](https://www.adafruit.com/product/4755) does not provide such capability, I needed external battery monitor. Of course, ideally connected via STEMMA QT. Initially, for some reason, I chose [Adafruit LC709203F LiPoly / LiIon Fuel Gauge and Battery Monitor](https://www.adafruit.com/product/4712) even though it is no longer manufactured. This posed a bunch of challenges, in particular not being able to get the data from the sensor due to [some weird ESP/CircuitPython bug](https://forums.adafruit.com/viewtopic.php?p=947796), so I rather went with the newer [Adafruit MAX17048 gauge](https://www.adafruit.com/product/5580) instead.

To avoid charging the LiPo battery when freezing, I needed to solder a thermistor to the charger.

### Packaging

Initially, it was just the ESP32 connected to external solar charger. Then I added temperature sensor, then swapped the ESP32 for another with external antenna, added solar charger, battery gauge and suddently it's a bunch of connected circuits.

Will need to find a way how to neatly package it all inside the radiation shield.

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
