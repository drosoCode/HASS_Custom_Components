"""Support for pollens"""
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

    add_entities([PollenSensor(dep, tree) for tree in monitored], True)


class PollenSensor(Entity):
    """Representation of a pollen level."""

    def __init__(self, dep, tree):
        """Initialize the sensor."""
        self._dep = dep
        self._title = tree
        treeList = ["general","tilleul","ambroisies","olivier","plantain","noisetier","aulne","armoise","chataigner","urticacees","oseille","graminees","chene","platane","bouleau","charme","peuplier","frene","saule","cypres"]
        try:
            self._id = treeList.index(tree)
        except ValueError:
            _LOGGER.error("Device type not available")
            return

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
        resp = self.getPollensApiData(self._dep)
        self._state = self.getTextLevel(self._id)
        self._text = resp[self._id] 

    def getPollensApiData(self,dep):    
        data = requests.get("https://www.pollens.fr/risks/thea/counties/"+str(dep))
        rep = json.loads(data.text)
        pollens = []
        pollens.append(rep["riskLevel"])
        for risk in rep["risks"]:
            pollens.append(risk["level"])
        return pollens
    
    def getTextLevel(self,level):
        if level is 0:
            text = "Risque Nul"
        elif level is 1:
            text = "Risque Tres Faible"
        elif level is 2:
            text = "Risque Faible"
        elif level is 3:
            text = "Risque Moyen"
        elif level is 4:
            text = "Risque Eleve"
        elif level is 5:
            text = "Risque Tres Eleve"
        else:
            text = "Erreur"
        return text
