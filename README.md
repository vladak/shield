# shield

Originally, this contained code for ESP32 Adafruit Feather to measure temperature and send it to MQTT broker,
however during the course of getting this up and running, I discovered 
[serious issue](https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/issues/115) with 
[Adafruit MQTT library](https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/)
or CircuitPython so this branch contains code to reproduce this.

The `secrets.py` file should contain stuff like this:
```python
secrets = {
    "ssid": "foo",
    "password": "bar",
    "broker": "172.40.0.3",
    "broker_port": 4444,
}
```
