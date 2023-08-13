"""
Module with code for temperature/humidity sensor reading.
"""
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


def get_measurements(i2c):
    """
    Acquire temperature, humidity and CO2 measurements. Try various sensors,
    prefer higher precision measurements.
    Return tuple of humidity, temperature and CO2 (either can be None).
    """

    logger = logging.getLogger("")

    temperature = None
    try:
        tmp117 = adafruit_tmp117.TMP117(i2c)
        temperature = tmp117.temperature
        logger.debug("Acquired temperature from tmp117")
    except NameError:
        logger.info("No library for the tmp117 sensor")

    humidity = None
    try:
        sht40 = adafruit_sht4x.SHT4x(i2c)
        if not temperature:
            temperature = sht40.temperature
            logger.debug("Acquired temperature from sht40")
        humidity = sht40.relative_humidity
        logger.debug("Acquired humidity from sht40")
    except NameError:
        logger.info("No library for the sht40 sensor")

    try:
        aht20 = adafruit_ahtx0.AHTx0(i2c)
        # Prefer temperature measurement from the tmp117/sht40 as they have higher accuracy.
        if not temperature:
            temperature = aht20.temperature
            logger.debug("Acquired temperature from aht20")
        # Prefer humidity measurement from sht40 as it has higher accuracy.
        if not humidity:
            humidity = aht20.relative_humidity
            logger.debug("Acquired humidity from aht20")
    except NameError:
        logger.info("No library for the ath20 sensor")

    co2_ppm = None
    try:
        scd4x_sensor = adafruit_scd4x.SCD4X(i2c)
        co2_ppm = scd4x_sensor.CO2
        if co2_ppm:
            logger.debug(f"CO2 ppm={co2_ppm}")
    except ValueError as exception:
        logger.error(f"cannot find SCD4x sensor: {exception}")
    except NameError:
        logger.info("No library for the scd4x sensor")

    return humidity, temperature, co2_ppm
