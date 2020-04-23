"""Support for urlPlayer"""
import logging
import requests
import urllib.parse

import voluptuous as vol

from homeassistant.components.media_player import (
    MediaPlayerDevice, PLATFORM_SCHEMA)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC, SUPPORT_PLAY_MEDIA, SUPPORT_STOP)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, STATE_OFF, STATE_PAUSED,
    STATE_PLAYING)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_PLAYURL = 'playUrl'
CONF_STOPURL = 'stopUrl'
CONF_NAME = 'name'

SUPPORT_URLPlayer = SUPPORT_PLAY_MEDIA | SUPPORT_STOP

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_PLAYURL): cv.string,
    vol.Required(CONF_STOPURL): cv.string,
    vol.Required(CONF_NAME): cv.string
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the MPD platform."""
    playUrl = config.get(CONF_PLAYURL)
    stopUrl = config.get(CONF_STOPURL)
    name = config.get(CONF_NAME)

    device = urlPlayerDevice(name, playUrl, stopUrl)
    add_entities([device], True)


class urlPlayerDevice(MediaPlayerDevice):

    # pylint: disable=no-member
    def __init__(self, name, playUrl, stopUrl):
        self._playUrl = playUrl
        self._stopUrl = stopUrl
        self._name = name
        parsedUrl = urllib.parse.urlparse(playUrl)
        self._pingUrl = parsedUrl.scheme+"://"+parsedUrl.netloc
    
    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_URLPlayer
        
    @property
    def available(self):
        """Return true if device is available and connected."""
        if requests.get(self._pingUrl).status_code == requests.codes.ok:
            return True
        else:
            return False

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    def media_stop(self):
        requests.get(self._stopUrl)

    def play_media(self, media_type, media_id, **kwargs):
        """Send the media player the command for playing a playlist."""
        if media_type == MEDIA_TYPE_MUSIC:
            mediaUrl = urllib.parse.quote(media_id, safe='')
            requests.get(self._playUrl+mediaUrl)
        else:
            _LOGGER.error("media type %s is not supported", media_type)
