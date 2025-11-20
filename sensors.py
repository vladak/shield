"""
Module with code for temperature/humidity/CO2/light sensor reading.
Works only for sensors connected via I2C (STEMMA QT).

The following sensors are supported:
  - TMP117
  - SHT40
  - AHT20
  - BME280
  - SCD-40
  - VEML-7700

If multiple temperature/humidity sensors are present, the values are taken based
on priority given by the list above, from highest to lowest.
"""

import time

try:
    from typing import Dict, Optional, Tuple, Union
except ImportError:
    pass

import adafruit_logging as logging

try:
    import adafruit_tmp117
except ImportError:
    pass
try:
    import adafruit_ahtx0
except ImportError:
    pass
try:
    import adafruit_sht4x
except ImportError:
    pass
try:
    import adafruit_scd4x
except ImportError:
    pass
try:
    from adafruit_bme280 import basic as adafruit_bme280
except ImportError:
    pass
try:
    import adafruit_veml7700
except ImportError:
    pass


# pylint: disable=too-few-public-methods
class Sensors:
    """Sensor abstraction"""

    # pylint: disable=too-many-statements,too-many-branches
    def __init__(self, i2c, light_gain=None) -> None:
        """
        Initialize the sensor objects. Assumes I2C.
        """
        logger = logging.getLogger("")

        self.tmp117 = None
        try:
            self.tmp117 = adafruit_tmp117.TMP117(i2c)
            logger.info("TMP117 sensor initialized")
        except NameError:
            logger.info("No library for the tmp117 sensor")
        except ValueError as value_exc:
            logger.info(f"No tmp117 sensor found: {value_exc}")

        self.sht40 = None
        try:
            self.sht40 = adafruit_sht4x.SHT4x(i2c)
            logger.info("SHT40 initialized")
        except NameError:
            logger.info("No library for the sht40 sensor")
        except ValueError as value_exc:
            logger.info(f"No sht40 sensor found: {value_exc}")

        self.aht20 = None
        try:
            self.aht20 = adafruit_ahtx0.AHTx0(i2c)
            logger.info("AHT20 sensor initialized")
        except NameError:
            logger.info("No library for the ath20 sensor")
        except ValueError as value_exc:
            logger.info(f"No ath20 sensor found: {value_exc}")

        self.bme280 = None
        try:
            self.bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)
            logger.info("BME280 sensor initialized")
        except NameError:
            logger.info("No library for the bme280 sensor")
        except ValueError as value_exc:
            logger.info(f"No bme280 sensor found: {value_exc}")

        self.scd4x_sensor = None
        try:
            self.scd4x_sensor = adafruit_scd4x.SCD4X(i2c)
            if self.scd4x_sensor:
                logger.info("Waiting for the first measurement from the SCD-40 sensor")
                self.scd4x_sensor.start_periodic_measurement()
            logger.info("SCD-40 sensor initialized")
        except ValueError as exception:
            logger.error(f"cannot find SCD4x sensor: {exception}")
        except NameError:
            logger.info("No library for the scd4x sensor")

        self.veml_sensor = None
        try:
            self.veml_sensor = adafruit_veml7700.VEML7700(i2c)
            if light_gain is not None:
                if light_gain == 1:
                    light_gain = adafruit_veml7700.VEML7700.ALS_GAIN_1
                elif light_gain == 2:
                    light_gain = adafruit_veml7700.VEML7700.ALS_GAIN_2
                else:
                    raise ValueError(f"invalid light gain value: {light_gain}")
                self.veml_sensor.light_gain = light_gain
        except ValueError as exception:
            logger.error(f"cannot find VEML7700 sensor: {exception}")
        except NameError:
            logger.info("No library for the VEML7700 sensor")

    # pylint: disable=too-many-branches
    def get_measurements(
        self,
    ) -> Tuple[
        float | int | type[None],
        float | int | type[None],
        int | type[None],
        int | type[None],
    ]:
        """
        Acquire temperature, humidity, CO2 and lux measurements.
        Try various sensors, prefer higher precision measurements.
        Some of the sensors return temperature as integer, while some as float.
        Return tuple of humidity, temperature, CO2, lux (either can be None).
        """

        logger = logging.getLogger("")

        temperature = None
        if self.tmp117:
            temperature = self.tmp117.temperature
            logger.debug("Acquired temperature from tmp117")

        humidity = None
        if self.sht40:
            if not temperature:
                temperature = self.sht40.temperature
                logger.debug("Acquired temperature from sht40")
            humidity = self.sht40.relative_humidity
            logger.debug("Acquired humidity from sht40")

        if self.aht20:
            # Prefer temperature measurement from the tmp117/sht40 as they have higher accuracy.
            if not temperature:
                temperature = self.aht20.temperature
                logger.debug("Acquired temperature from aht20")
            # Prefer humidity measurement from sht40 as it has higher accuracy.
            if not humidity:
                humidity = self.aht20.relative_humidity
                logger.debug("Acquired humidity from aht20")

        if self.bme280:
            if not temperature:
                temperature = self.bme280.temperature
                logger.debug("Acquired temperature from bme280")
            if not humidity:
                humidity = self.bme280.relative_humidity
                logger.debug("Acquired humidity from bme280")

        co2_ppm = None
        if self.scd4x_sensor:
            for _ in range(0, 5):
                while not self.scd4x_sensor.data_ready:
                    logger.debug("Sleeping for half second")
                    time.sleep(0.5)

            co2_ppm = self.scd4x_sensor.CO2
            if co2_ppm:
                logger.debug(f"CO2 ppm={co2_ppm}")

            if not temperature:
                temperature = self.scd4x_sensor.temperature
                logger.debug("Acquired temperature from SCD4x")

            if not humidity:
                humidity = self.scd4x_sensor.relative_humidity
                logger.debug("Acquired humidity from SCD4x")

        lux = None
        if self.veml_sensor:
            lux = self.veml_sensor.lux
            logger.debug("Acquired illuminance from VEML7700")

        return humidity, temperature, co2_ppm, lux

    def get_measurements_dict(self) -> Dict:
        """
        Put the metrics into dictionary and return it.
        """
        data = {}
        logger = logging.getLogger("")

        humidity, temperature, co2_ppm, lux = self.get_measurements()

        if temperature:
            logger.info(f"Temperature: {temperature:.1f} C")
            data["temperature"] = f"{temperature:.1f}"
        if humidity:
            logger.info(f"Humidity: {humidity:.1f} %")
            data["humidity"] = f"{humidity:.1f}"
        if co2_ppm:
            logger.info(f"CO2 = {co2_ppm} ppm")
            data["co2_ppm"] = f"{co2_ppm}"
        if lux:
            logger.info(f"light = {lux} lux")
            data["lux"] = f"{lux}"

        logger.debug(f"data: {data}")
        return data
