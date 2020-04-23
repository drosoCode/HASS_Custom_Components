"""Support for urlPlayer"""
import requests
import urllib.parse

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC, SUPPORT_PLAY_MEDIA, SUPPORT_STOP)
from . import (
    CONF_HOST, CONF_NAME, NabaztagEntity)
import homeassistant.helpers.config_validation as cv

SUPPORT_URLPlayer = SUPPORT_PLAY_MEDIA | SUPPORT_STOP

async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
        
    if discovery_info is None:
        return

    host = discovery_info[CONF_HOST]
    name = discovery_info[CONF_NAME]

    async_add_entities([nabaztagPlayer(name, host)], True)

class nabaztagPlayer(NabaztagEntity, MediaPlayerDevice):

    # pylint: disable=no-member
    def __init__(self, name, host):
        super().__init__(host)
        self._playUrl = self._host+"/play?u="
        self._stopUrl = self._host+"/stop"
        self._name = name
    
    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_URLPlayer
        
    @property
    def name(self):
        """Return the name of the device."""
        return self._name+"_player"

    def media_stop(self):
        requests.get(self._stopUrl)

    def play_media(self, media_type, media_id, **kwargs):
        """Send the media player the command for playing a playlist."""
        if media_type == MEDIA_TYPE_MUSIC:
            mediaUrl = urllib.parse.quote(media_id, safe='')
            requests.get(self._playUrl+mediaUrl)
