"""Support for Nabaztag."""

from . import (
    CONF_HOST, CONF_NAME, NabaztagEntity)
from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_EFFECT, SUPPORT_BRIGHTNESS, SUPPORT_EFFECT, Light)

import requests

async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
        
    if discovery_info is None:
        return

    host = discovery_info[CONF_HOST]
    name = discovery_info[CONF_NAME]
    switches = ['earLeft','earRight','ledNose','ledInfo','up']

    all_switches = []

    for setting in switches:
        all_switches.append(NabaztagLight(name, host, setting))

    async_add_entities(all_switches, True)


class NabaztagLight(NabaztagEntity, Light):

    def __init__(self, name, host, setting):
        """Initialize the settings switch."""
        super().__init__(host)
        self._name = name
        self._setting = setting
        self._brightness = 0
        self._state = True
        if setting == 'earLeft' or setting == 'earRight' or setting == 'up':
            self._custom_effects = {}
        else:
            if setting == 'ledNose':
                self._custom_effects = {'OFF':'0','On':'1','Todo':'2','Urgent':'3','Panic':'4'}
            elif setting == 'ledInfo':
                self._custom_effects = {'OFF':'clear','wSun':'weather?v=0','wClouds':'weather?v=1','wFog':'weather?v=2','wRain':'weather?v=3','wSnow':'weather?v=4','wStrom':'weather?v=5','sMin3':'stock?v=0','sMin2':'stock?v=1','sMin1':'stock?v=2','s0':'stock?v=3','s1':'stock?v=4','s2':'stock?v=5','s3':'stock?v=6','tFree':'traffic?v=0','tOk':'traffic?v=1','tModerate':'traffic?v=2','tNormal':'traffic?v=3','tHeavy':'traffic?v=4','tCongested':'traffic?v=5','tExtreme':'traffic?v=6','p0':'pollution?v=0','p1':'pollution?v=1','p2':'pollution?v=2','p3':'pollution?v=3','p4':'pollution?v=4','p5':'pollution?v=5','p6':'pollution?v=6','p7':'pollution?v=7','p8':'pollution?v=8','p9':'pollution?v=9','p10':'pollution?v=10'}

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
        elif self._setting == 'ledInfo' or self._setting == 'ledNose':
            SUPPORT = (SUPPORT_EFFECT)
        else:
            SUPPORT = 0
        return SUPPORT

    
    @property
    def effect_list(self):
        """Return the list of supported effects."""
        return self.custom_effects_names

    @property
    def custom_effects(self):
        """Return dict with custom effects."""
        return self._custom_effects

    @property
    def custom_effects_names(self):
        """Return list with custom effects names."""
        return list(self.custom_effects.keys())

    def turn_on(self, **kwargs) -> None:
        """Turn the bulb on."""
        self._state = True
        if self._setting == 'up':
            requests.get(self._host+"/wakeup")
        elif self._setting == 'earLeft':
            self._brightness = kwargs.get(ATTR_BRIGHTNESS)
            requests.get(self._host+"/left?p="+str(round(self._brightness/255*16))+"&d=0")
        elif self._setting == 'earRight':
            self._brightness = kwargs.get(ATTR_BRIGHTNESS)
            requests.get(self._host+"/right?p="+str(round(self._brightness/255*16))+"&d=0")
        elif self._setting == 'ledInfo':
            requests.get(self._host+"/"+self._custom_effects[kwargs.get(ATTR_EFFECT)])
        elif self._setting == 'ledNose':
            requests.get(self._host+"/nose?v="+self._custom_effects[kwargs.get(ATTR_EFFECT)])
        else:
            pass 


    def turn_off(self, **kwargs) -> None:
        """Turn off."""
        if self._setting == 'up':
            self._state = False
            requests.get(self._host+"/sleep")
        elif self._setting == 'earLeft':
            requests.get(self._host+"/left?p=0&d=0")
        elif self._setting == 'earRight':
            requests.get(self._host+"/right?p=0&d=0")
        elif self._setting == 'ledNose':
            requests.get(self._host+"/nose?v=0")
        elif self._setting == 'ledInfo':
            requests.get(self._host+"/clear")
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
        elif self._setting == 'ledNose':
            return 'mdi:bell-alert'
        elif self._setting == 'ledInfo':
            return 'mdi:decagram'
        else:
            return 'mdi:flash'
