"""Support for karotz."""

from . import (
    CONF_HOST, CONF_NAME, karotzEntity)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_HS_COLOR, SUPPORT_BRIGHTNESS, SUPPORT_COLOR, Light)
from homeassistant.util import color

import requests
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
        
    if discovery_info is None:
        return

    host = discovery_info[CONF_HOST]
    name = discovery_info[CONF_NAME]
    switches = ['earLeft','earRight','ledInfo','up']

    all_switches = []

    for setting in switches:
        all_switches.append(karotzLight(hass, name, host, setting))

    async_add_entities(all_switches, True)


class karotzLight(karotzEntity, Light):

    def __init__(self, hass, name, host, setting):
        
        super().__init__(host)
        self._name = name
        self._setting = setting
        self._brightness = 0
        self._state = True
        self._color = "000000"
        self._hass = hass
            
    @property
    def name(self):
        """Return the name of the node."""
        return self._name+"_"+self._setting

    @property
    def is_on(self):
        """Return the boolean response if the node is on."""
        return self._state

    @property
    def brightness(self):
        return self._brightness

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        if self._setting == 'earLeft' or self._setting == 'earRight':
            SUPPORT = (SUPPORT_BRIGHTNESS)
        elif self._setting == 'ledInfo':
            SUPPORT = (SUPPORT_BRIGHTNESS | SUPPORT_COLOR)
        else:
            SUPPORT = 0
        return SUPPORT

    def turn_on(self, **kwargs) -> None:
        """Turn the bulb on."""
        self._state = True
        if self._setting == 'up':
            requests.get(self._host+"/cgi-bin/wakeup?silent=1")
        
        elif self._setting == 'earLeft':
            self._brightness = kwargs.get(ATTR_BRIGHTNESS)
            otherBrightness = self._hass.states.get('light.'+self._name+"_earRight").attributes['brightness']
            requests.get(self._host+"/cgi-bin/ears?left="+str(round(self._brightness/255*16))+"&right="+str(round(otherBrightness/255*16))+"&noreset=1")
        
        elif self._setting == 'earRight':
            self._brightness = kwargs.get(ATTR_BRIGHTNESS)
            otherBrightness = self._hass.states.get('light.'+self._name+"_earLeft").attributes['brightness']
            requests.get(self._host+"/cgi-bin/ears?left="+str(round(otherBrightness/255*16))+"&right="+str(round(self._brightness/255*16))+"&noreset=1")
        
        elif self._setting == 'ledInfo':
            brightness = kwargs.get(ATTR_BRIGHTNESS)
            if brightness is not None:
                self._brightness = brightness

            colorAttr = kwargs.get(ATTR_HS_COLOR)
            if colorAttr is not None:
                self._color = colorAttr

            colorRGB = color.color_hs_to_RGB(self._color[0],self._color[1])
            colorData = color.color_rgb_to_hex(colorRGB[0],colorRGB[1],colorRGB[2])
            
            if self._brightness < 15:
                requests.get(self._host+"/cgi-bin/leds?color="+str(colorData))
            else:
                requests.get(self._host+"/cgi-bin/leds?pulse=1&color="+str(colorData)+"&speed="+str(round(self._brightness/255*2000))+"&color2=000000")
        else:
            pass


    def turn_off(self, **kwargs) -> None:
        """Turn off."""
        if self._setting == 'up':
            self._state = False
            requests.get(self._host+"/cgi-bin/sleep")
        elif self._setting == 'earLeft' or self._setting == 'earRight':
            requests.get(self._host+"/cgi-bin/ears_reset")
        elif self._setting == 'ledInfo':
            requests.get(self._host+"/cgi-bin/leds?color=000000")
        else:
            pass
    
    @property
    def icon(self):
        """Return the icon for the light."""
        if self._setting == 'up':
            return 'mdi:access-point'
        elif self._setting == 'earLeft':
            return 'mdi:arrow-top-left-bottom-right-bold'
        elif self._setting == 'earRight':
            return 'mdi:arrow-top-right-bottom-left-bold'
        elif self._setting == 'ledInfo':
            return 'mdi:decagram'
        else:
            return 'mdi:flash'
