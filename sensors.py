"""
Module with code for temperature/humidity sensor reading.
"""

import time

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


# pylint: disable=too-few-public-methods
class Sensors:
    """Sensor abstraction"""

    def __init__(self, i2c):
        """
        Initialize the sensor objects.
        """
        logger = logging.getLogger("")

        self.tmp117 = None
        try:
            self.tmp117 = adafruit_tmp117.TMP117(i2c)
        except NameError:
            logger.info("No library for the tmp117 sensor")

        self.sht40 = None
        try:
            self.sht40 = adafruit_sht4x.SHT4x(i2c)
        except NameError:
            logger.info("No library for the sht40 sensor")

        self.aht20 = None
        try:
            self.aht20 = adafruit_ahtx0.AHTx0(i2c)
        except NameError:
            logger.info("No library for the ath20 sensor")

        self.scd4x_sensor = None
        try:
            self.scd4x_sensor = adafruit_scd4x.SCD4X(i2c)
            if self.scd4x_sensor:
                logger.info("Waiting for the first measurement from the SCD-40 sensor")
                self.scd4x_sensor.start_periodic_measurement()
        except ValueError as exception:
            logger.error(f"cannot find SCD4x sensor: {exception}")
        except NameError:
            logger.info("No library for the scd4x sensor")

    def get_measurements(self):
        """
        Acquire temperature, humidity and CO2 measurements. Try various sensors,
        prefer higher precision measurements.
        Return tuple of humidity, temperature and CO2 (either can be None).
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

        co2_ppm = None
        if self.scd4x_sensor:
            for _ in range(0, 5):
                while not self.scd4x_sensor.data_ready:
                    logger.debug("Sleeping for half second")
                    time.sleep(0.5)

            co2_ppm = self.scd4x_sensor.CO2
            if co2_ppm:
                logger.debug(f"CO2 ppm={co2_ppm}")

        return humidity, temperature, co2_ppm
