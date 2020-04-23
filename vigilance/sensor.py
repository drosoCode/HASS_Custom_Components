"""Support for vigilance"""
import logging
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

import requests
import xmltodict

_LOGGER = logging.getLogger(__name__)

ATTR_TEXT = 'type'
CONF_DEP = 'dep'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DEP): cv.string
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the vigilance platform."""
    dep = config.get(CONF_DEP)

    add_entities([VigilanceSensor(dep, 1),VigilanceSensor(dep, 2)], True)


class VigilanceSensor(Entity):
    """Representation of a vigilance level."""

    def __init__(self, dep, vType):
        """Initialize the sensor."""
        self._dep = dep
        self._vType = vType

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Vigilance:"+str(self._vType)

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
        resp = self.getData(self._dep)
        if self._vType == 1:
            self._state = self.getTextFromNum(resp[0])
            self._text = self.getRiskFromNum(resp[2])
        else:
            self._state = self.getTextFromNum(resp[1])
            self._text = ""

    def getData(self,dep):
        data = xmltodict.parse(requests.get("http://vigilance.meteofrance.com/data/NXFR34_LFPW_.xml").text)["cartevigilance"]["datavigilance"]
        couleur = 0
        crue = 0
        risque = 0
        for depData in data:
            if depData["@dep"] == str(dep):
                couleur = depData["@couleur"]
                if "crue" in depData:
                    crue = depData["crue"]["@valeur"]
                if "risque" in depData:
                    risque = depData["risque"]["@valeur"]
                break
        return [couleur,crue,risque]
    
    def getTextFromNum(self,color):
        if color == "1":
            text = "Risque Faible"
        elif color == "2":
            text = "Risque Modere"
        elif color == "3":
            text = "Risque Eleve"
        elif color == "4":
            text = "Risque Tres Eleve"
        else:
            text = "Erreur"
        return text

    def getRiskFromNum(self,num):
        if num == "1":
            text = "Vent"
        elif num == "2":
            text = "Pluie-Inondation"
        elif num == "3":
            text = "Orages"
        elif num == "4":
            text = "Innondations"
        elif num == "5":
            text = "Neige-Verglas"
        elif num == "6":
            text = "Canicule"
        elif num == "7":
            text = "Grand-Froid"
        else:
            text = "RAS"
        return text
