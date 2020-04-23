"""Support for Android IP Webcam."""
import asyncio
import logging
import requests

import voluptuous as vol

from homeassistant.core import callback
from homeassistant.const import (
    CONF_NAME, CONF_HOST)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import (
    async_dispatcher_send, async_dispatcher_connect)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'karotz'

DEFAULT_NAME = 'karotz1'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.All(cv.ensure_list, [vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_HOST): cv.string,
    })])
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):

    async def async_setup_nabz(nabz_config):
        
        host = nabz_config[CONF_HOST]
        name = nabz_config[CONF_NAME]
        
        hass.async_create_task(discovery.async_load_platform(
            hass, 'light', DOMAIN, {
                CONF_NAME: name,
                CONF_HOST: host
            }, config))
        
        hass.async_create_task(discovery.async_load_platform(
            hass, 'media_player', DOMAIN, {
                CONF_NAME: name,
                CONF_HOST: host
            }, config))
        

    tasks = [async_setup_nabz(conf) for conf in config[DOMAIN]]
    if tasks:
        await asyncio.wait(tasks)

    return True


class karotzEntity(Entity):
    """The karotz device """

    def __init__(self, host):
        """Initialize the data object."""
        self._host = "http://"+host

    @property
    def should_poll(self):
        """Return True if entity has to be polled for state."""
        return False

    @property
    def available(self):
        """Return True if entity is available."""
        return True
        
