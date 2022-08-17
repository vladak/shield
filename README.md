# shield
code for ESP32 Adafruit Feather to measure temperature and send it to MQTT broker

This is used specifically on [Adafruit ESP32-S2 Feather with BME280 Sensor](https://www.adafruit.com/product/5303). 
This looked to be a fine all-in-one package, however initial experiments with temperature
readings using the built-in BME280 sensor showed that the skew of the metric due to the board being warmed up by 
the WiFi/SoC chip is too high - for ambient temperature of twenty/thirty-ish degrees of Celsius, the sensor
readings were forty-ish degrees of Celsius even though the code ran every couple of minutes to let the circuitry cool down.

This, I bought the [Adafruit TMP117 ±0.1°C High Accuracy I2C Temperature Sensor](https://www.adafruit.com/product/4821),
connected via STEMMA QT and this works fine.

This repository is called 'shield' as an allude to [Stevenson screen](https://en.wikipedia.org/wiki/Stevenson_screen) because
the Feather with the sensor is placed into a plastic screen.
