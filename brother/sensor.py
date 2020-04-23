"""Support for the Brother printer ink status."""
import logging
import voluptuous as vol
from homeassistant.const import CONF_HOST
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

from bs4 import BeautifulSoup
import requests

_LOGGER = logging.getLogger(__name__)

ATTR_TITLE = 'level'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Brother platform."""

    printer_ip = config.get(CONF_HOST, [])

    try:
        rawData = requests.get('http://'+printer_ip+'/general/status.html')
    except:
        _LOGGER.error("Printer not available")
        return

    i = 0
    while i<4:
        add_entities([BrotherSensor(printer_ip,i)], True)
        i+=1


class BrotherSensor(Entity):
    """Representation of a cartridge level."""

    def __init__(self, printer_ip, id):
        """Initialize the sensor."""
        self._rawData = requests.get('http://'+printer_ip+'/general/status.html')
        self._id = id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._title

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:chart-donut'

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return "%"

    # pylint: disable=no-member
    def update(self):
        """Update device state."""
        soup = BeautifulSoup(self._rawData.text, "html")
        data = soup.table.contents[1].contents
        i = 0
        while i<self._id+1:
            self._title = data[i].contents[0].attrs["alt"]
            self._state = int(data[i].contents[0].attrs["height"])*2
            i+=1
