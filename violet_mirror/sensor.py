"""Support for reading data from mirror."""
import logging
import binascii
from aiofile import AIOFile

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_DEVICE, CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "mirror1"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_DEVICE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

#/dev/mirror
#add KERNEL=="hidraw*", ATTRS{idVendor}=="1da8", ATTRS{idProduct}=="1301", SYMLINK+="mirror", MODE="066
#in /etc/udev/rules.d/mirror.rules
#check presence with: dmesg | grep Mirror    or        ls /dev/hidraw1

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the mirror platform."""
    name = config.get(CONF_NAME)
    device = config.get(CONF_DEVICE)

    sensor = MirrorSensor(hass, name, device)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, sensor.stop_serial_read())
    async_add_entities([sensor], True)


class MirrorSensor(Entity):
    """Representation of a Mirror sensor."""

    def __init__(self, hass, name, device):
        """Initialize the Mirror sensor."""
        self._name = name
        self._continue = True
        self._state = "None"
        self._device = device
        self.hass = hass
        self._serial_loop_task = self.hass.loop.create_task(
            self.async_read_loop()
        )

    async def async_read_loop(self, **kwargs):
        """Read the data from the port."""
        async with AIOFile(self._device, 'rb') as afp:
            while self._continue:
                data = await afp.read(16)
                rfid_id = binascii.hexlify(data)[4:]
                if data != b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' and rfid_id != b'0000000000000000000000000000':
                    if data[0:2] == b'\x02\x01':
                        newState = "+"+rfid_id.decode("utf-8")#nanoztag added
                    elif data[0:2] == b'\x02\x02':
                        newState = "-"+rfid_id.decode("utf-8")#nanoztag removed

                    if newState != self._state:
                        self._state = newState
                        self.async_schedule_update_ha_state()
            

    async def stop_serial_read(self):
        """Close resources."""
        self._continue = False
        if self._serial_loop_task:
            self._serial_loop_task.cancel()
        self._reader.close()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
