"""Support for moustiques"""
import logging
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

import requests
import json

_LOGGER = logging.getLogger(__name__)

ATTR_TEXT = 'level'
CONF_MONITORED = 'monitored_conditions'
CONF_DEP = 'dep'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEP): cv.string,
    vol.Required(CONF_MONITORED, default=[]):
        vol.All(cv.ensure_list, [cv.string]),
})



def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Pollen platform."""    
    monitored = config.get(CONF_MONITORED, [])
    dep = config.get(CONF_DEP)

    add_entities([MosquitoSensor(dep, mtype) for mtype in monitored], True)


class MosquitoSensor(Entity):
    """Representation of a pollen level."""

    def __init__(self, dep, mType):
        """Initialize the sensor."""
        self._dep = dep
        self._title = mType
        if mType == "tiger":
            self._mType = "2"
        else:
            self._mType = "1"

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
        return 'mdi:alert'
    
    @property
    def should_poll(self):
        """Device should be polled."""
        return True
    
    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_TEXT: self._text
        }

    # pylint: disable=no-member
    def update(self):
        resp = self.getDataFromColor(self.getData(self._dep,self._mType))
        self._state = resp[1]
        self._text = resp[0]

    def getData(self,dep,mType):
        #type: 1 = moustique ; 2 = moustique tigre
        data = json.loads(requests.get("http://vigilance-moustiques.com/maps-manager/public/json/"+str(mType)).text)["alertes"]
        mStatus = ""
        for colorType in data:
            for department in data[colorType]:
                if department == str(dep):
                    mStatus = colorType
                    break
        return mStatus

    def getDataFromColor(self,color):
        code = 0
        text = "Risque Tres Faible"
        if color == "jaune":
            code = 1
            text = "Risque Faible"
        elif color == "orange":
            code = 2
            text = "Rique Modere"
        elif color == "rouge":
            code = 3
            text = "Risque Eleve"
        elif color == "pourpre":
            code = 4
            text = "Risque Tres Eleve"
        return [code,text]
