"""Support for myjdownloader"""
import logging
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

import requests
from datetime import timedelta

#BASED ON https://github.com/Cubiss/myjdapi
###################################### myjdapi imports ###################
import hashlib
import hmac
import json
import time
try:
    # from urllib.request import urlopen
    from urllib.parse import quote
except:                         #For Python 2
    from urllib import quote
    # from urllib import urlopen
import base64
import requests
#from Crypto.Cipher import AES
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
BS = 16
#########################################################################


#################################### myjdapi code ######################


class MYJDException(BaseException):
    pass


def PAD(s):
    try:
        return s + ((BS - len(s) % BS) * chr(BS - len(s) % BS)).encode()
    except:                     # For python 2
        return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)

def UNPAD(s):
    try:
        return s[0:-s[-1]]
    except:                     # For python 2
        return s[0:-ord(s[-1])]

class System:
    """
    Class that represents the system-functionality of a Device
    """
    def __init__(self, device):
        self.device = device
        self.url = '/system'

    def exit_jd(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/exitJD")
        return resp

    def restart_jd(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/restartJD")
        return resp

    def hibernate_os(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/hibernateOS")
        return resp

    def shutdown_os(self, force):
        """
        :param force:  Force Shutdown of OS
        :return:
        """
        params = force
        resp = self.device.action(self.url + "/shutdownOS", params)
        return resp

    def standby_os(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/standbyOS")
        return resp
        
class Jd:
    """
    Class that represents the jd-functionality 
    """
    def __init__(self, device):
        self.device = device
        self.url = '/jd'

    def get_uptime(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/uptime")
        return resp

    def get_version(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/version")
        return resp

    def get_core_revision(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/getCoreRevision")
        return resp
        
class Update:
    """
    Class that represents the update-functionality of a Device
    """
    def __init__(self, device):
        self.device = device
        self.url = '/update'

    def restart_and_update(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/restartAndUpdate")
        return resp

    def run_update_check(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/runUpdateCheck")
        return resp

    def is_update_available(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/isUpdateAvailable")
        return resp
        
class DownloadController:
    """
    Class that represents the download-controller of a Device
    """
    def __init__(self, device):
        self.device = device
        self.url = '/downloadcontroller'

    def start_downloads(self):
        """
        :return:
        """
        resp = self.device.action(self.url+"/start")
        return resp

    def stop_downloads(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/stop")
        return resp

    def pause_downloads(self, value):
        """
        :param value:
        :return:
        """
        params = [value]
        resp = self.device.action(self.url + "/pause", params)
        return resp

    def get_speed_in_bytes(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/getSpeedInBps")
        return resp

    def force_download(self, link_ids, package_ids):
        """
        :param link_ids:
        :param package_ids:
        :return:
        """
        params = [link_ids, package_ids]
        resp = self.device.action(self.url + "/forceDownload", params)
        return resp

    def get_current_state(self):
        """
        :return:
        """
        resp = self.device.action(self.url + "/getCurrentState")
        return resp

class Linkgrabber:
    """
    Class that represents the linkgrabber of a Device
    """
    def __init__(self, device):
        self.device = device
        self.url = '/linkgrabberv2'

    def clear_list(self):
        """
        Clears Linkgrabbers list
        """
        resp = self.device.action(self.url+"/clearList", http_action="POST")
        return resp

    def move_to_downloadlist(self, links_ids, packages_ids):
        """
        Moves packages and/or links to download list.
        :param packages: Packages UUID.
        :type: list of strings.
        :param links: Links UUID.
        """
        params = [links_ids,packages_ids]
        resp = self.device.action(self.url+"/moveToDownloadlist", params)
        return resp

    def query_links(self, params=[
            {
                "bytesTotal"    : True,
                "comment"       : True,
                "status"        : True,
                "enabled"       : True,
                "maxResults"    : -1,
                "startAt"       : 0,
                "hosts"         : True,
                "url"           : True,
                "availability"  : True,
                "variantIcon"   : True,
                "variantName"   : True,
                "variantID"     : True,
                "variants"      : True,
                "priority"      : True
            }]):
        """
        Get the links in the linkcollector/linkgrabber
        :param params: A dictionary with options. The default dictionary is
        configured so it returns you all the downloads with all details, but you
        can put your own with your options. All the options available are this
        ones:
        {
        "bytesTotal"    : false,
        "comment"       : false,
        "status"        : false,
        "enabled"       : false,
        "maxResults"    : -1,
        "startAt"       : 0,
        "packageUUIDs"  : null,
        "hosts"         : false,
        "url"           : false,
        "availability"  : false,
        "variantIcon"   : false,
        "variantName"   : false,
        "variantID"     : false,
        "variants"      : false,
        "priority"      : false
        }
        :type: Dictionary
        :rtype: List of dictionaries of this style, with more or less detail based on your options.
        [   {   'availability': 'ONLINE',
            'bytesTotal': 68548274,
            'enabled': True,
            'name': 'The Rick And Morty Theory - The Original        Morty_ - '
                    'Cartoon Conspiracy (Ep. 74) @ChannelFred (192kbit).m4a',
            'packageUUID': 1450430888524,
            'url': 'youtubev2://DEMUX_M4A_192_720P_V4/d1NZf1w2BxQ/',
            'uuid': 1450430889576,
            'variant': {   'id': 'DEMUX_M4A_192_720P_V4',
                        'name': '192kbit/s M4A-Audio'},
            'variants': True
            }, ... ]
        """
        resp = self.device.action(self.url+"/queryLinks", params)
        return resp

    def cleanup(self,  action, mode, selection_type, links_ids=[], packages_ids=[] ):
        """
        Clean packages and/or links of the linkgrabber list.
        Requires at least a packages_ids or links_ids list, or both.
        :param packages_ids: Packages UUID.
        :type: list of strings.
        :param links_ids: Links UUID.
        :type: list of strings
        :param action: Action to be done. Actions: DELETE_ALL, DELETE_DISABLED, DELETE_FAILED, DELETE_FINISHED, DELETE_OFFLINE, DELETE_DUPE, DELETE_MODE
        :type: str:
        :param mode: Mode to use. Modes: REMOVE_LINKS_AND_DELETE_FILES, REMOVE_LINKS_AND_RECYCLE_FILES, REMOVE_LINKS_ONLY
        :type: str:
        :param selection_type: Type of selection to use. Types: SELECTED, UNSELECTED, ALL, NONE
        :type: str:
        """
        params = [links_ids,packages_ids]
        params += [action,mode,selection_type]
        resp = self.device.action(self.url+"/cleanup", params)
        return resp

    def add_container(self, type_, content):
        """
        Adds a container to Linkgrabber.
        :param type_: Type of container.
        :type: string.
        :param content: The container.
        :type: string.
        """
        params = [type_, content]
        resp = self.device.action(self.url+"/addContainer", params)
        return resp

    def get_download_urls(self, links_ids, packages_ids, url_display_type):
        """
        Gets download urls from Linkgrabber.
        :param packages_ids: Packages UUID.
        :type: List of strings.
        :param Links_ids: Links UUID.
        :type: List of strings
        :param url_display_type: No clue. Not documented
        :type: Dictionary
        """
        params = [packages_ids, links_ids, url_display_type]
        resp = self.device.action(self.url+"/getDownloadUrls", params)
        return resp

    def set_priority(self, priority, links_ids, packages_ids ):
        """
        Sets the priority of links or packages.
        :param packages_ids: Packages UUID.
        :type: list of strings.
        :param links_ids: Links UUID.
        :type: list of strings
        :param priority: Priority to set. Priorities: HIGHEST, HIGHER, HIGH, DEFAULT, LOWER;
        :type: str:
        """
        params = [priority, links_ids, packages_ids]
        resp = self.device.action(self.url+"/setPriority", params)
        return resp

    def set_enabled(self, params):
        """
        My guess is that it Enables/Disables a download, but i haven't got it working.
        :param params: List with a boolean (enable/disable download), my guess
        the parameters are package uuid, download uuid. Ex:
        [False,2453556,2334455].
        :type: List
        :rtype:
        """
        resp = self.device.action(self.url+"/setEnabled", params)
        return resp

    def get_variants(self, params):
        """
        Gets the variants of a url/download (not package), for example a youtube
        link gives you a package with three downloads, the audio, the video and
        a picture, and each of those downloads have different variants (audio
        quality, video quality, and picture quality).
        :param params: List with the UUID of the download you want the variants. Ex: [232434]
        :type: List
        :rtype: Variants in a list with dictionaries like this one: [{'id':
        'M4A_256', 'name': '256kbit/s M4A-Audio'}, {'id': 'AAC_256', 'name':
        '256kbit/s AAC-Audio'},.......]
        """
        resp = self.device.action(self.url+"/getVariants", params)
        return resp

    def add_links(self, params=[
            {
                "autostart" : False,
                "links" : None,
                "packageName" : None,
                "extractPassword" : None,
                "priority" : "DEFAULT",
                "downloadPassword" : None,
                "destinationFolder" : None,
                "overwritePackagizerRules" : False
            }]):
        """
        Add links to the linkcollector
        {
        "autostart" : false,
        "links" : null,
        "packageName" : null,
        "extractPassword" : null,
        "priority" : "DEFAULT",
        "downloadPassword" : null,
        "destinationFolder" : null
        }
        """
        resp = self.device.action("/linkgrabberv2/addLinks", params)
        return resp

    def get_childrenchanged(self):
        """
        no idea what parameters i have to pass and/or i don't know what it does.
        if i find out i will implement it :p
        """
        pass

    def remove_links(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def get_downfolderhistoryselectbase(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def help(self):
        """
        It returns the API help.
        """
        resp = self.device.action("/linkgrabberv2/help",http_action="GET")
        return resp

    def rename_link(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def move_links(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def set_variant(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def get_package_count(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def rename_package(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def query_packages(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def move_packages(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

    def add_variant_copy(self):
        """
        No idea what parameters i have to pass and/or i don't know what it does.
        If i find out i will implement it :P
        """
        pass

class Downloads:
    """
    Class that represents the downloads list of a Device
    """
    def __init__(self, device):
        self.device = device
        self.url = "/downloadsV2"

    def query_links(self, params=[
            {
                "bytesTotal" : True,
                "comment" : True,
                "status" : True,
                "enabled" : True,
                "maxResults" : -1,
                "startAt" : 0,
                "packageUUIDs" : [],
                "host" : True,
                "url" : True,
                "bytesloaded" : True,
                "speed" : True,
                "eta" : True,
                "finished" : True,
                "priority" : True,
                "running" : True,
                "skipped" : True,
                "extractionStatus" : True
            }]):
        """
        Get the links in the download list
        """
        resp = self.device.action(self.url+"/queryLinks", params)
        return resp

    def query_packages(self, params=[
            {
                "bytesLoaded" : True,
                "bytesTotal" : True,
                "comment" : True,
                "enabled" : True,
                "eta" : True,
                "priority" : True,
                "finished" : True,
                "running" : True,
                "speed" : True,
                "status" : True,
                "childCount" : True,
                "hosts" : True,
                "saveTo" : True,
                "maxResults" : -1,
                "startAt" : 0,
            }]):
        """
        Get the packages in the download list
        """
        resp = self.device.action(self.url+"/queryPackages", params)
        return resp

    def cleanup(self,  action, mode, selection_type, links_ids=[], packages_ids=[] ):
        """
        Clean packages and/or links of the linkgrabber list.
        Requires at least a packages_ids or links_ids list, or both.
        :param packages_ids: Packages UUID.
        :type: list of strings.
        :param links_ids: Links UUID.
        :type: list of strings
        :param action: Action to be done. Actions: DELETE_ALL, DELETE_DISABLED, DELETE_FAILED, DELETE_FINISHED, DELETE_OFFLINE, DELETE_DUPE, DELETE_MODE
        :type: str:
        :param mode: Mode to use. Modes: REMOVE_LINKS_AND_DELETE_FILES, REMOVE_LINKS_AND_RECYCLE_FILES, REMOVE_LINKS_ONLY
        :type: str:
        :param selection_type: Type of selection to use. Types: SELECTED, UNSELECTED, ALL, NONE
        :type: str:
        """
        params = [links_ids,packages_ids]
        params += [action,mode,selection_type]
        resp = self.device.action(self.url+"/cleanup", params)
        return resp

class Jddevice:
    """
    Class that represents a JDownloader device and it's functions
    """
    def __init__(self, jd, device_dict):
        """ This functions initializates the device instance.
        It uses the provided dictionary to create the device.
        :param device_dict: Device dictionary
        """
        self.name = device_dict["name"]
        self.device_id = device_dict["id"]
        self.device_type = device_dict["type"]
        self.myjd = jd
        self.linkgrabber = Linkgrabber(self)
        self.downloads = Downloads(self)
        self.downloadcontroller = DownloadController(self)
        self.update = Update(self)
        self.system = System(self)
        self.jd = Jd(self)

    def action(self, path, params=(), http_action="POST"):
        """Execute any action in the device using the postparams and params.
        All the info of which params are required and what are they default value, type,etc
        can be found in the MY.Jdownloader API Specifications ( https://goo.gl/pkJ9d1 ).
        :param params: Params in the url, in a list of tuples. Example:
        /example?param1=ex&param2=ex2 [("param1","ex"),("param2","ex2")]
        :param postparams: List of Params that are send in the post.
        """
        action_url = self.__action_url()
        response = self.myjd.request_api(path, http_action, params, action_url)
        if response is None:
            return False
        return response['data']

    def __action_url(self):
        return "/t_"+self.myjd.get_session_token()+"_"+self.device_id

class Myjdapi:
    """
    Main class for connecting to JD API.
    """
    def __init__(self):
        """
        This functions initializates the myjdapi object.
        """
        self.__request_id = int(time.time()*1000)
        self.__api_url = "http://api.jdownloader.org"
        self.__app_key = "http://git.io/vmcsk"
        self.__api_version = 1
        self.__devices = None
        self.__login_secret = None
        self.__device_secret = None
        self.__session_token = None
        self.__regain_token = None
        self.__server_encryption_token = None
        self.__device_encryption_token = None
        self.__connected = False

    def get_session_token(self):
        return self.__session_token

    def is_connected(self):
        """
        Indicates if there is a connection established.
        """
        return self.__connected

    def set_app_key(self, app_key):
        """
        Sets the APP Key.
        """
        self.__app_key = app_key

    def __secret_create(self, email, password, domain):
        """
        Calculates the login_secret and device_secret
        :param email: My.Jdownloader User email
        :param password: My.Jdownloader User password
        :param domain: The domain , if is for Server (login_secret) or Device (device_secret)
        :return: secret hash
        """
        secret_hash = hashlib.sha256()
        secret_hash.update(email.lower().encode('utf-8') + password.encode('utf-8') + \
                    domain.lower().encode('utf-8'))
        return secret_hash.digest()

    def __update_encryption_tokens(self):
        """
        Updates the server_encryption_token and device_encryption_token
        """
        if self.__server_encryption_token is None:
            old_token = self.__login_secret
        else:
            old_token = self.__server_encryption_token
        new_token = hashlib.sha256()
        new_token.update(old_token + bytearray.fromhex(self.__session_token))
        self.__server_encryption_token = new_token.digest()
        new_token = hashlib.sha256()
        new_token.update(self.__device_secret+bytearray.fromhex(self.__session_token))
        self.__device_encryption_token = new_token.digest()

    def __signature_create(self,key,data):
        """
        Calculates the signature for the data given a key.
        :param key:
        :param data:
        """
        signature = hmac.new(key, data.encode('utf-8'), hashlib.sha256)
        return signature.hexdigest()
    """
    def __decrypt(self,secret_token,data):
        Decrypts the data from the server using the provided token
        :param secret_token:
        :param data:
        init_vector = secret_token[:len(secret_token)//2]
        key = secret_token[len(secret_token)//2:]
        decryptor = AES.new(key, AES.MODE_CBC, init_vector)
        decrypted_data = UNPAD(decryptor.decrypt(base64.b64decode(data)))
        return decrypted_data

    def __encrypt(self,secret_token,data):
        Encrypts the data from the server using the provided token
        :param secret_token:
        :param data:
        data = PAD(data.encode('utf-8'))
        init_vector = secret_token[:len(secret_token)//2]
        key = secret_token[len(secret_token)//2:]
        encryptor = AES.new(key, AES.MODE_CBC, init_vector)
        encrypted_data = base64.b64encode(encryptor.encrypt(data))
        return encrypted_data.decode('utf-8')
    """
    def __decrypt(self,secret_token,data):
        """
        Decrypts the data from the server using the provided token
        :param secret_token:
        :param data:
        """
        backend = default_backend()
        iv = secret_token[:len(secret_token)//2]
        key = secret_token[len(secret_token)//2:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        decrypted_data = UNPAD(decryptor.update(base64.b64decode(data)) + decryptor.finalize())
        return decrypted_data

    def __encrypt(self,secret_token,data):
        """
        Encrypts the data from the server using the provided token
        :param secret_token:
        :param data:
        """
        backend = default_backend()
        data = PAD(data.encode('utf-8'))
        iv = secret_token[:len(secret_token)//2]
        key = secret_token[len(secret_token)//2:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
        encryptor = cipher.encryptor()
        ct = encryptor.update(data) + encryptor.finalize()
        encrypted_data = base64.b64encode(ct)
        return encrypted_data.decode('utf-8')

    def update_request_id(self):
        """
        Updates Request_Id
        """
        self.__request_id = int(time.time())

    def connect(self, email, password):
        """Establish connection to api
        :param email: My.Jdownloader User email
        :param password: My.Jdownloader User password
        :returns: boolean -- True if succesful, False if there was any error.
        """
        self.__login_secret = self.__secret_create(email, password, "server")
        self.__device_secret = self.__secret_create(email, password, "device")
        response = self.request_api("/my/connect", "GET",[("email", email), ("appkey", self.__app_key)])
        self.__connected = True
        self.update_request_id()
        self.__session_token = response["sessiontoken"]
        self.__regain_token = response["regaintoken"]
        self.__update_encryption_tokens()
        self.update_devices()

    def reconnect(self):
        """
        Reestablish connection to API.
        :returns: boolean -- True if successful, False if there was any error.
        """
        response = self.request_api("/my/reconnect", "GET",[("sessiontoken", self.__session_token), ("regaintoken", self.__regain_token)])
        self.update_request_id()
        self.__session_token = response["sessiontoken"]
        self.__regain_token = response["regaintoken"]
        self.__update_encryption_tokens()

    def disconnect(self):
        """
        Disconnects from  API
        :returns: boolean -- True if successful, False if there was any error.
        """
        response = self.request_api("/my/disconnect", "GET", [("sessiontoken", self.__session_token)])
        self.update_request_id()
        self.__login_secret = None
        self.__device_secret = None
        self.__session_token = None
        self.__regain_token = None
        self.__server_encryption_token = None
        self.__device_encryption_token = None
        self.__devices = None
        self.__connected = False

    def update_devices(self):
        """
        Updates available devices. Use list_devices() to get the devices list.
        :returns: boolean -- True if successful, False if there was any error.
        """
        response = self.request_api("/my/listdevices", "GET",[("sessiontoken",self.__session_token)])
        self.update_request_id()
        self.__devices = response["list"]

    def list_devices(self):
        """
        Returns available devices. Use getDevices() to update the devices list.
        Each device in the list is a dictionary like this example:
        {
            'name': 'Device',
            'id': 'af9d03a21ddb917492dc1af8a6427f11',
            'type': 'jd'
        }
        :returns: list -- list of devices.
        """
        return self.__devices

    def get_device(self, device_name=None, device_id=None):
        """
        Returns a jddevice instance of the device
        :param deviceid:
        """
        if not self.is_connected() :
            raise(MYJDException("No connection established\n"))
        if device_id is not None:
            for device in self.__devices:
                if device["id"] == device_id:
                    return Jddevice(self, device)
        elif device_name is not None:
            for device in self.__devices:
                if device["name"] == device_name:
                    return Jddevice(self, device)
        raise(MYJDException("Device not found\n"))

    def request_api(self, path, http_method="GET",params=None, action=None):
        """
        Makes a request to the API to the 'path' using the 'http_method' with parameters,'params'.
        Ex:
        http_method=GET
        params={"test":"test"}
        post_params={"test2":"test2"}
        action=True
        This would make a request to "http://api.jdownloader.org/"
        """
        data = None
        if not self.is_connected() and path != "/my/connect":
            raise(MYJDException("No connection established\n"))
        if http_method == "GET":
            query = [path + "?"]
            for param in params:
                if param[0] != "encryptedLoginSecret":
                    query += ["%s=%s" % (param[0], quote(param[1]))]
                else:
                    query += ["&%s=%s" % (param[0], param[1])]
            query += ["rid="+str(self.__request_id)]
            if self.__server_encryption_token is None:
                query += ["signature=" + \
                          str(self.__signature_create(self.__login_secret, query[0]+"&".join(query[1:])))]
            else:
                query += ["signature=" + \
                          str(self.__signature_create(self.__server_encryption_token, query[0]+"&".join(query[1:])))]
            query = query[0]+"&".join(query[1:])
            encrypted_response = requests.get(self.__api_url+query)
        else:
            params_request=[]
            for param in params:
                if not isinstance(param,list):
                    # params_request+=[str(param).replace("'",'\"').replace("True","true").replace("False","false").replace('None',"null")]
                    params_request+=[json.dumps(param)]
                else:
                    params_request+=[param]
            params_request = {"apiVer": self.__api_version, "url" : path, "params":params_request, "rid":self.__request_id}
            data = json.dumps(params_request).replace('"null"',"null").replace("'null'","null")
            encrypted_data = self.__encrypt(self.__device_encryption_token,data)
            if action is not None:
                request_url=self.__api_url+action+path
            else:
                request_url=self.__api_url+path
            encrypted_response = requests.post(request_url,headers={"Content-Type": "application/aesjson-jd; charset=utf-8"},data=encrypted_data)
        if encrypted_response.status_code != 200:
            error_msg=json.loads(encrypted_response.text)
            msg="\n\tSOURCE: "+error_msg["src"]+"\n\tTYPE: "+ \
                                error_msg["type"]+"\n------\nREQUEST_URL: "+ \
                                self.__api_url+path
            if http_method == "GET":
                msg+=query
            msg+="\n"
            if data is not None:
                msg+="DATA:\n"+data
            raise(MYJDException(msg))
        if action is None:
            if not self.__server_encryption_token:
                response = self.__decrypt(self.__login_secret, encrypted_response.text)
            else:
                response = self.__decrypt(self.__server_encryption_token, encrypted_response.text)
        else:
            if params is not None:
                response = self.__decrypt(self.__device_encryption_token, encrypted_response.text)
            else:
                return {"data" : response}
        jsondata = json.loads(response.decode('utf-8'))
        if jsondata['rid'] != self.__request_id:
            self.update_request_id()
            return None
        self.update_request_id()
        return jsondata


########################################################################
########################################################################




_LOGGER = logging.getLogger(__name__)

ATTR_TEXT = 'level'
CONF_MONITORED = 'monitored_conditions'
CONF_USER = 'user'
CONF_PASS = 'password'
CONF_JDID = 'id'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USER): cv.string,
    vol.Required(CONF_PASS): cv.string,
    vol.Required(CONF_JDID): cv.string,
    vol.Required(CONF_MONITORED, default=[]):
        vol.All(cv.ensure_list, [cv.string]),
})



def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the myjdownloader platform."""    
    monitored = config.get(CONF_MONITORED, [])
    user = config.get(CONF_USER)
    passw = config.get(CONF_PASS)
    jdId = config.get(CONF_JDID)

    add_entities([DownloadSensor(user, passw, jdId, dType) for dType in monitored], True)


class DownloadSensor(Entity):
    """Representation of a download level."""

    def __init__(self, user, passw, jdId, dType):
        """Initialize the sensor."""
        self._user = user
        self._passw = passw
        self._jdId = jdId
        types = ["totalToDowload","totalDownloaded","packagesNbr","enabledPackagesNbr","finishedPackagesNbr","failedPackagesNbr","waitingPackagesNbr","errorRate","downloadedRate","status","downloadSpeed","totalEta","runningPackages","currentDownload","gbText","packagesText"]
        units = ["gb","gb","","","","","","%","%","","mb/s","d/h/min","","","",""]

        try:
            self._id = types.index(dType)
        except ValueError:
            _LOGGER.error("Device type not available")
            return
        self._title = dType
        self._unit = units[self._id]
        
        #totalToDowload (gb); totalDownloaded (gb); packagesNbr; enabledPackagesNbr; finishedPackagesNbr; 
        #failedPackagesNbr; waitingPackagesNbr; errorRate; downloadedRate; status downloadSpeed (mb/s); totalEta (d/h/min/sec); 
        # runningPackages; currentDownload; gbText; packagesText

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
        return 'mdi:download'
    
    @property
    def should_poll(self):
        """Device should be polled."""
        return True

    # pylint: disable=no-member
    def update(self):
        resp = self.getData(self._user,self._passw,self._jdId)
        self._state = resp[self._id]
    
    def getData(self,user,passw,jdID):
        #jd=myjdapi.Myjdapi()
        jd=Myjdapi()
        jd.set_app_key("HomeAssistant")

        jd.connect(user,passw)
        jd.update_devices()
        device=jd.get_device(device_id=jdID)

        packages = device.downloads.query_packages([{
                        "bytesLoaded" : True,
                        "bytesTotal" : True,
                        "comment" : False,
                        "enabled" : True,
                        "eta" : True,
                        "priority" : False,
                        "finished" : True,
                        "running" : True,
                        "speed" : False,
                        "status" : True,
                        "childCount" : False,
                        "hosts" : False,
                        "saveTo" : False,
                        "maxResults" : -1,
                        "startAt" : 0,
                    }])

        totalBytes = 0
        loadedBytes = 0
        packageNbr = 0
        enabledPackages = 0
        totalEta = 0
        finishedPackages = 0
        failedPackages = 0
        waitingPackages = 0
        runningPackages = 0
        currentDownload = "None"
        #print(packages)

        while packageNbr<len(packages):
            totalBytes += packages[packageNbr]["bytesTotal"]
            loadedBytes += packages[packageNbr]["bytesLoaded"]
            if packages[packageNbr]["enabled"]:
                enabledPackages += 1
            if "finished" in packages[packageNbr] and packages[packageNbr]["finished"]:
                finishedPackages += 1
            if "status" in packages[packageNbr] and "Erreur" in packages[packageNbr]["status"]:
                failedPackages += 1
            if "status" in packages[packageNbr] and "Limit" in packages[packageNbr]["status"]:
                waitingPackages += 1
            if "running" in packages[packageNbr]:
                runningPackages += 1
                currentDownload = packages[packageNbr]["name"]
            if "eta" in packages[packageNbr]:
                totalEta += packages[packageNbr]["eta"]
            packageNbr += 1

        totalToDL = round((totalBytes/1024/1024/1024),3)
        totalDLd = round((loadedBytes/1024/1024/1024),3)
        return [totalToDL,totalDLd,packageNbr,enabledPackages,finishedPackages,failedPackages,waitingPackages,round((failedPackages/packageNbr*100),1),round((finishedPackages/packageNbr*100),1),device.downloadcontroller.get_current_state(),round((device.downloadcontroller.get_speed_in_bytes()/1024/1024),2),str(timedelta(seconds=totalEta)),runningPackages,currentDownload,str(totalDLd)+"/"+str(totalToDL),str(finishedPackages)+"/"+str(packageNbr)]
