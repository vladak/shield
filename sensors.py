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


def get_measurements(i2c):
    """
    Acquire temperature and humidity measurements. Try various sensors,
    prefer higher precision measurements.
    Return tuple of humidity and temperature (either can be None).
    """

    logger = logging.getLogger(__name__)

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

    return humidity, temperature
