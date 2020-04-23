"""Support for prevair"""
import logging
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_LATITUDE, CONF_LONGITUDE)

#import long and lat

import requests
import json
import math
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

CONF_MONITORED = 'monitored_conditions'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED, default=[]):
        vol.All(cv.ensure_list, [cv.string]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Pollen platform."""    
    monitored = config.get(CONF_MONITORED, [])

    lat = float(config.get(CONF_LATITUDE, hass.config.latitude))
    long = float(config.get(CONF_LONGITUDE, hass.config.latitude))
    add_entities([PollutionSensor(lat, long, polluant) for polluant in monitored], True)


class PollutionSensor(Entity):
    """Representation of a pollution level."""

    def __init__(self, lat, long, polluant):
        """Initialize the sensor."""
        self._lat = lat
        self._long = long
        self._title = polluant
        self._isAtmo = False

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
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        if self._isAtmo:
            return ""
        else:
            return "ppm"
    
    @property
    def should_poll(self):
        """Device should be polled."""
        return True

    # pylint: disable=no-member
    def update(self):
        data = self.getData(self._lat,self._long,self._title)
        self._state = data[0]
        self._isAtmo = data[2]

    def getData(self,lat,long,polluant):
        date = datetime.now().strftime('%Y-%m-%d')
        data_url = "http://www2.prevair.org/ineris-web-services.php?url=mesureJourna&date="+date+"&code_polluant="
        atmo_url = "http://www2.prevair.org/ineris-web-services.php?url=atmo&date="+date

        #polluant peut etre: a_INDICE, a_SO2, a_NO2, a_O3, a_PM10, CO, SO2, NO2, O3, PM10, PM25, j_CO, j_SO2, j_NO2, j_O3, j_PM10, j_PM25
        #rajouter a_ pour indice ATMO ; rajouter j_ pour moyenne journaliere ; max horaire par defaut
        isAtmo = False
        if "a_" in polluant:
            polluant = polluant[2:]
            mode = "atmo"
            isAtmo = True
            code = self.getPolluantCode(polluant,True)
            data = json.loads(requests.get(atmo_url).text)
        elif "j_" in polluant:
            polluant = polluant[2:]
            mode = "data_day"
            code = self.getPolluantCode(polluant,False)
            data = json.loads(requests.get(data_url+code).text)
        else:
            mode = "data_hour"
            code = self.getPolluantCode(polluant,False)
            data = json.loads(requests.get(data_url+code).text)

        i = 1
        distMin = 2000000
        
        while i != len(data):
            if isAtmo:          
                distance = self.getDistance(lat, long, data[i][2], data[i][3])
                if distMin > distance:
                    distMin = distance
                    stationData = data[i][code]
                    stationName = data[i][13]
            else:
                distance = self.getDistance(lat, long, data[i][2], data[i][1])
                if distMin > distance:
                    distMin = distance
                    if mode is "data_day":
                        stationData = data[i][6]
                    else:
                        stationData = data[i][5]
                    stationName = data[i][0]
            i+=1
        return [stationData,stationName,isAtmo]

    def getPolluantCode(self,polluant,isAtmo=False):
        if isAtmo:
            if polluant == "SO2":
                code = 8
            elif polluant == "NO2":
                code = 9
            elif polluant == "O3":
                code = 10
            elif polluant == "PM10":
                code = 11
            elif polluant == "INDICE":
                code = 7
            else:
                code  = -1
        else:
            if polluant == "CO":
                code = "04"
            elif polluant == "SO2":
                code = "01"
            elif polluant == "NO2":
                code = "03"
            elif polluant == "O3":
                code = "08"
            elif polluant == "PM10":
                code = "24"
            elif polluant == "PM25":
                code = "39"
            else:
                code = "-1"
        return code

    def getDistance(self,lat1, lng1, lat2, lng2):
        earth_radius = 6378137
        rlo1 = math.radians(float(lng1))
        rla1 = math.radians(float(lat1))
        rlo2 = math.radians(float(lng2))
        rla2 = math.radians(float(lat2))
        dlo = (rlo2 - rlo1) / 2
        dla = (rla2 - rla1) / 2
        a = (math.sin(dla) * math.sin(dla)) + math.cos(rla1) * math.cos(rla2) * (math.sin(dlo) * math.sin(dlo))
        d = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round((earth_radius * d)/1000)

