"""Support for Niu Scooters by Marcel Westra."""
from datetime import datetime, timedelta
import json
import logging
from time import gmtime, strftime

import hashlib
import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_MONITORED_VARIABLES
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

ACCOUNT_BASE_URL = "https://account.niu.com"
LOGIN_URI = "/v3/api/oauth2/token"
API_BASE_URL = "https://app-api.niu.com"
MOTOR_BATTERY_API_URI = "/v3/motor_data/battery_info"
MOTOR_INDEX_API_URI = "/v5/scooter/motor_data/index_info"
MOTOINFO_LIST_API_URI = "/v5/scooter/list"
MOTOINFO_ALL_API_URI = "/motoinfo/overallTally"
TRACK_LIST_API_URI = "/v5/track/list/v2"

DOMAIN = "niu"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCOOTER_ID = "scooter_id"

DEFAULT_SCOOTER_ID = 0

SENSOR_TYPE_BAT = "BAT"
SENSOR_TYPE_MOTO = "MOTO"
SENSOR_TYPE_DIST = "DIST"
SENSOR_TYPE_OVERALL = "TOTAL"
SENSOR_TYPE_POS = "POSITION"
SENSOR_TYPE_TRACK = "TRACK"

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCOOTER_ID, default=DEFAULT_SCOOTER_ID): cv.positive_int,
        vol.Optional(CONF_MONITORED_VARIABLES, default=["BatteryCharge"]): vol.All(
            cv.ensure_list,
            vol.Length(min=1),
            [
                vol.In(
                    [
                        "BatteryCharge",
                        "Isconnected",
                        "TimesCharged",
                        "temperatureDesc",
                        "Temperature",
                        "BatteryGrade",
                        "CurrentSpeed",
                        "ScooterConnected",
                        "IsCharging",
                        "IsLocked",
                        "TimeLeft",
                        "EstimatedMileage",
                        "centreCtrlBatt",
                        "HDOP",
                        "Longitude",
                        "Latitude",
                        "Distance",
                        "RidingTime",
                        "totalMileage",
                        "DaysInUse",
                        "LastTrackStartTime",
                        "LastTrackEndTime",
                        "LastTrackDistance",
                        "LastTrackAverageSpeed",
                        "LastTrackRidingtime",
                        "LastTrackThumb",
                    ]
                )
            ],
        ),
    }
)

SENSOR_TYPES = {
    "BatteryCharge": [
        "battery_charge",
        "%",
        "batteryCharging",
        SENSOR_TYPE_BAT,
        "battery",
        "mdi:battery-charging-50",
    ],
    "Isconnected": [
        "is_connected",
        "",
        "isConnected",
        SENSOR_TYPE_BAT,
        "connectivity",
        "mdi:connection",
    ],
    "TimesCharged": [
        "times_charged",
        "x",
        "chargedTimes",
        SENSOR_TYPE_BAT,
        "none",
        "mdi:battery-charging-wireless",
    ],
    "temperatureDesc": [
        "temp_descr",
        "",
        "temperatureDesc",
        SENSOR_TYPE_BAT,
        "none",
        "mdi:thermometer-alert",
    ],
    "Temperature": [
        "temperature",
        "°C",
        "temperature",
        SENSOR_TYPE_BAT,
        "temperature",
        "mdi:thermometer",
    ],
    "BatteryGrade": [
        "battery_grade",
        "%",
        "gradeBattery",
        SENSOR_TYPE_BAT,
        "battery",
        "mdi:car-battery",
    ],
    "CurrentSpeed": [
        "current_speed",
        "km/h",
        "nowSpeed",
        SENSOR_TYPE_MOTO,
        "none",
        "mdi:speedometer",
    ],
    "ScooterConnected": [
        "scooter_connected",
        "",
        "isConnected",
        SENSOR_TYPE_MOTO,
        "connectivity",
        "mdi:motorbike-electric",
    ],
    "IsCharging": [
        "is_charging",
        "",
        "isCharging",
        SENSOR_TYPE_MOTO,
        "power",
        "mdi:battery-charging",
    ],
    "IsLocked": ["is_locked", "", "lockStatus", SENSOR_TYPE_MOTO, "lock", "mdi:lock"],
    "TimeLeft": [
        "time_left",
        "h",
        "leftTime",
        SENSOR_TYPE_MOTO,
        "none",
        "mdi:av-timer",
    ],
    "EstimatedMileage": [
        "estimated_mileage",
        "km",
        "estimatedMileage",
        SENSOR_TYPE_MOTO,
        "none",
        "mdi:map-marker-distance",
    ],
    "centreCtrlBatt": [
        "centre_ctrl_batt",
        "%",
        "centreCtrlBattery",
        SENSOR_TYPE_MOTO,
        "battery",
        "mdi:car-cruise-control",
    ],
    "HDOP": ["hdp", "", "hdop", SENSOR_TYPE_MOTO, "none", "mdi:map-marker"],
    "Longitude": ["long", "", "lng", SENSOR_TYPE_POS, "none", "mdi:map-marker"],
    "Latitude": ["lat", "", "lat", SENSOR_TYPE_POS, "none", "mdi:map-marker"],
    "Distance": [
        "distance",
        "m",
        "distance",
        SENSOR_TYPE_DIST,
        "none",
        "mdi:map-marker-distance",
    ],
    "RidingTime": [
        "riding_time",
        "s",
        "ridingTime",
        SENSOR_TYPE_DIST,
        "none",
        "mdi:map-clock",
    ],
    "totalMileage": [
        "total_mileage",
        "km",
        "totalMileage",
        SENSOR_TYPE_OVERALL,
        "none",
        "mdi:map-marker-distance",
    ],
    "DaysInUse": [
        "bind_days_count",
        "days",
        "bindDaysCount",
        SENSOR_TYPE_OVERALL,
        "none",
        "mdi:calendar-today",
    ],
    "LastTrackStartTime": [
        "last_track_start_time",
        "",
        "startTime",
        SENSOR_TYPE_TRACK,
        "none",
        "mdi:clock-start",
    ],
    "LastTrackEndTime": [
        "last_track_end_time",
        "",
        "endTime",
        SENSOR_TYPE_TRACK,
        "none",
        "mdi:clock-end",
    ],
    "LastTrackDistance": [
        "last_track_distance",
        "m",
        "distance",
        SENSOR_TYPE_TRACK,
        "none",
        "mdi:map-marker-distance",
    ],
    "LastTrackAverageSpeed": [
        "last_track_average_speed",
        "km/h",
        "avespeed",
        SENSOR_TYPE_TRACK,
        "none",
        "mdi:speedometer",
    ],
    "LastTrackRidingtime": [
        "last_track_riding_time",
        "",
        "ridingtime",
        SENSOR_TYPE_TRACK,
        "none",
        "mdi:timelapse",
    ],
    "LastTrackThumb": [
        "last_track_thumb",
        "",
        "track_thumb",
        SENSOR_TYPE_TRACK,
        "none",
        "mdi:map",
    ]
}


def get_token(username, password):
    url = ACCOUNT_BASE_URL + LOGIN_URI
    md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
    data = {
        "account": username,
        "password": md5,
        "grant_type": "password",
        "scope": "base",
        "app_id": "niu_ktdrr960",
    }
    try:
        r = requests.post(url, data=data)
    except BaseException as e:
        print(e)
        return False
    data = json.loads(r.content.decode())
    return data["data"]["token"]["access_token"]


def get_vehicles_info(path, token):
    url = API_BASE_URL + path
    headers = {"token": token}
    try:
        r = requests.get(url, headers=headers, data=[])
    except ConnectionError:
        return False
    if r.status_code != 200:
        return False
    data = json.loads(r.content.decode())
    return data


def get_info(path, sn, token):
    url = API_BASE_URL + path
    params = {"sn": sn}
    headers = {
        "token": token,
        "user-agent": "manager/4.6.48 (android; IN2020 11);lang=zh-CN;clientIdentifier=Domestic;timezone=Asia/Shanghai;model=IN2020;deviceName=IN2020;ostype=android",
    }
    try:
        r = requests.get(url, headers=headers, params=params)
    except ConnectionError:
        return False
    if r.status_code != 200:
        return False
    data = json.loads(r.content.decode())
    if data["status"] != 0:
        return False
    return data


def post_info(path, sn, token):
    url = API_BASE_URL + path
    params = {}
    headers = {"token": token, "Accept-Language": "en-US", "Content-Type": "application/json"}
    
    try:
        r = requests.post(url, headers=headers, params=params, json={"sn": sn})
    except ConnectionError as e:
        _LOGGER.error(f"post_info: ConnectionError occurred: {e}")
        return False
    except Exception as e:
        _LOGGER.error(f"post_info: Unexpected error occurred: {e}")
        return False
        
    if r.status_code != 200:
        _LOGGER.error(f"post_info: HTTP status code {r.status_code} is not 200")
        return False
        
    try:
        data = json.loads(r.content.decode())
        if data["status"] != 0:
            _LOGGER.error(f"post_info: API status {data['status']} is not 0. Response: {data}")
            return False
        return data
    except json.JSONDecodeError as e:
        _LOGGER.error(f"post_info: JSON decode error: {e}")
        return False
    except KeyError as e:
        _LOGGER.error(f"post_info: Missing key in response: {e}")
        return False
    except Exception as e:
        _LOGGER.error(f"post_info: Unexpected error parsing response: {e}")
        return False


def post_info_track(path, sn, token):
    url = API_BASE_URL + path
    params = {}
    headers = {
        "token": token,
        "Accept-Language": "en-US",
        "User-Agent": "manager/1.0.0 (identifier);clientIdentifier=identifier",
    }
    try:
        r = requests.post(
            url,
            headers=headers,
            params=params,
            json={"index": "0", "pagesize": 10, "sn": sn},
        )
    except ConnectionError:
        return False
    if r.status_code != 200:
        return False
    data = json.loads(r.content.decode())
    if data["status"] != 0:
        return False
    return data


def setup_platform(hass, config, add_devices, discovery_info=None):
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    scooter_id = config.get(CONF_SCOOTER_ID)
    api_uri = MOTOINFO_LIST_API_URI

    token, sn, sensor_prefix = _get_vehicle_info_with_retry(username, password, api_uri, scooter_id)
    if not all([token, sn, sensor_prefix]):
        _LOGGER.error("Failed to get vehicle information after all retries")
        return

    sensors = config.get(CONF_MONITORED_VARIABLES)
    data_bridge = _initialize_data_bridge_with_retry(sn, token)
    if not data_bridge:
        _LOGGER.error("Failed to initialize data bridge after all retries")
        return

    devices = _create_sensors_with_retry(data_bridge, sensors, sensor_prefix, sn)
    
    if devices:
        add_devices(devices)
        _LOGGER.info(f"Successfully added {len(devices)} NIU sensors")
    else:
        _LOGGER.error("No sensors were created successfully")


def _get_vehicle_info_with_retry(username, password, api_uri, scooter_id, max_retries=3, retry_delay=2):
    """Get vehicle information with retry mechanism"""
    for attempt in range(max_retries):
        try:
            _LOGGER.info(f"Attempt {attempt + 1}: Getting vehicle information...")
            
            token = get_token(username, password)
            if not token:
                _LOGGER.warning(f"Attempt {attempt + 1}: Failed to get authentication token")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                return None, None, None
            
            vehicles_info = get_vehicles_info(api_uri, token)
            if not vehicles_info or "data" not in vehicles_info or "items" not in vehicles_info["data"]:
                _LOGGER.warning(f"Attempt {attempt + 1}: Failed to get vehicles information")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                return None, None, None
            
            if scooter_id >= len(vehicles_info["data"]["items"]):
                _LOGGER.error(f"Scooter ID {scooter_id} is out of range. Available scooters: {len(vehicles_info['data']['items'])}")
                return None, None, None
            
            sn = vehicles_info["data"]["items"][scooter_id]["sn_id"]
            sensor_prefix = vehicles_info["data"]["items"][scooter_id]["scooter_name"]
            
            _LOGGER.info(f"Successfully connected to NIU scooter: {sensor_prefix} (SN: {sn})")
            return token, sn, sensor_prefix
            
        except Exception as e:
            _LOGGER.warning(f"Attempt {attempt + 1}: Error getting vehicle information: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                _LOGGER.error(f"Final attempt failed: {e}")
                return None, None, None
    
    return None, None, None


def _initialize_data_bridge_with_retry(sn, token, max_retries=3, retry_delay=2):
    """Initialize data bridge with retry mechanism"""
    for attempt in range(max_retries):
        try:
            _LOGGER.info(f"Attempt {attempt + 1}: Initializing data bridge...")
            
            data_bridge = NiuDataBridge(sn, token)
            
            data_bridge.updateBat()
            data_bridge.updateMoto()
            data_bridge.updateMotoInfo()
            data_bridge.updateTrackInfo()
            
            import time
            time.sleep(1)
            
            if data_bridge._dataMotoInfo and "data" in data_bridge._dataMotoInfo:
                available_fields = list(data_bridge._dataMotoInfo["data"].keys())
                _LOGGER.info(f"Available motor info fields: {available_fields}")
            else:
                _LOGGER.warning("Motor info data not available after update")
            
            _LOGGER.info("Data bridge initialized successfully")
            return data_bridge
            
        except Exception as e:
            _LOGGER.warning(f"Attempt {attempt + 1}: Error initializing data bridge: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(retry_delay)
            else:
                _LOGGER.error(f"Final attempt failed: {e}")
                return None
    
    return None


def _create_sensors_with_retry(data_bridge, sensors, sensor_prefix, sn, max_retries=2, retry_delay=1):
    """Create sensors with retry mechanism"""
    devices = []
    failed_sensors = []
    
    for sensor in sensors:
        sensor_created = False
        
        for attempt in range(max_retries):
            try:
                sensor_config = SENSOR_TYPES[sensor]
                device = NiuSensor(
                    data_bridge,
                    sensor,
                    sensor_config[0],
                    sensor_config[1],
                    sensor_config[2],
                    sensor_config[3],
                    sensor_prefix,
                    sensor_config[4],
                    sn,
                    sensor_config[5],
                )
                devices.append(device)
                sensor_created = True
                break
                
            except Exception as e:
                _LOGGER.warning(f"Attempt {attempt + 1}: Error creating sensor {sensor}: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    _LOGGER.error(f"Failed to create sensor {sensor} after all attempts")
                    failed_sensors.append(sensor)
        
        if not sensor_created:
            _LOGGER.warning(f"Sensor {sensor} will be skipped due to creation failure")
    
    if failed_sensors:
        _LOGGER.warning(f"Failed to create sensors: {', '.join(failed_sensors)}")
    
    return devices


class NiuDataBridge(object):
    def __init__(self, sn, token):
        self._dataBat = None
        self._dataMoto = None
        self._dataMotoInfo = None
        self._dataTrackInfo = None
        self._sn = sn
        self._token = token

    def dataBat(self, id_field):
        if not self._dataBat or "data" not in self._dataBat:
            return None
        return self._dataBat["data"]["batteries"]["compartmentA"][id_field]

    def dataMoto(self, id_field):
        if not self._dataMoto or "data" not in self._dataMoto:
            return None
        return self._dataMoto["data"][id_field]

    def dataDist(self, id_field):
        if not self._dataMoto or "data" not in self._dataMoto or "lastTrack" not in self._dataMoto["data"]:
            return None
        return self._dataMoto["data"]["lastTrack"][id_field]

    def dataPos(self, id_field):
        if not self._dataMoto or "data" not in self._dataMoto or "postion" not in self._dataMoto["data"]:
            return None
        return self._dataMoto["data"]["postion"][id_field]

    def dataOverall(self, id_field):
        if not self._dataMotoInfo or "data" not in self._dataMotoInfo:
            return None
        
        if id_field not in self._dataMotoInfo["data"]:
            return None
            
        return self._dataMotoInfo["data"][id_field]

    def dataTrack(self, id_field):
        if not self._dataTrackInfo or "data" not in self._dataTrackInfo or not self._dataTrackInfo["data"]:
            return None
        if id_field == "startTime" or id_field == "endTime":
            return datetime.fromtimestamp(
                (self._dataTrackInfo["data"][0][id_field]) / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
        if id_field == "ridingtime":
            return strftime(
                "%H:%M:%S", gmtime(self._dataTrackInfo["data"][0][id_field])
            )
        if id_field == "track_thumb":
            thumburl = self._dataTrackInfo["data"][0][id_field].replace(
                "app-api.niucache.com", "app-api.niu.com"
            )
            return thumburl
        return self._dataTrackInfo["data"][0][id_field]

    @Throttle(timedelta(seconds=1))
    def updateBat(self):
        self._dataBat = get_info(MOTOR_BATTERY_API_URI, self._sn, self._token)

    @Throttle(timedelta(seconds=1))
    def updateMoto(self):
        self._dataMoto = get_info(MOTOR_INDEX_API_URI, self._sn, self._token)

    @Throttle(timedelta(seconds=1))
    def updateMotoInfo(self):
        try:
            result = post_info(MOTOINFO_ALL_API_URI, self._sn, self._token)
            if result is False or result is None:
                return
            self._dataMotoInfo = result
        except Exception as e:
            _LOGGER.error(f"updateMotoInfo: Exception occurred: {e}")

    @Throttle(timedelta(seconds=1))
    def updateTrackInfo(self):
        self._dataTrackInfo = post_info_track(TRACK_LIST_API_URI, self._sn, self._token)


class NiuSensor(Entity):
    def __init__(
        self,
        data_bridge,
        name,
        sensor_id,
        uom,
        id_name,
        sensor_grp,
        sensor_prefix,
        device_class,
        sn,
        icon,
    ):
        self._unique_id = "sensor.niu_scooter_" + sn + "_" + sensor_id
        self._name = (
            "NIU Scooter " + sensor_prefix + " " + name
        )
        self._uom = uom
        self._data_bridge = data_bridge
        self._device_class = device_class
        self._id_name = id_name
        self._sensor_grp = sensor_grp
        self._icon = icon

        self._state = self._initialize_sensor_state()
        
    def _initialize_sensor_state(self, max_retries=3, retry_delay=2):
        """Initialize sensor state with retry mechanism"""
        for attempt in range(max_retries):
            try:
                if self._sensor_grp == SENSOR_TYPE_BAT:
                    state = self._data_bridge.dataBat(self._id_name)
                elif self._sensor_grp == SENSOR_TYPE_MOTO:
                    state = self._data_bridge.dataMoto(self._id_name)
                elif self._sensor_grp == SENSOR_TYPE_POS:
                    state = self._data_bridge.dataPos(self._id_name)
                elif self._sensor_grp == SENSOR_TYPE_DIST:
                    state = self._data_bridge.dataDist(self._id_name)
                elif self._sensor_grp == SENSOR_TYPE_OVERALL:
                    state = self._data_bridge.dataOverall(self._id_name)
                elif self._sensor_grp == SENSOR_TYPE_TRACK:
                    state = self._data_bridge.dataTrack(self._id_name)
                else:
                    state = None
                
                if state is not None:
                    return state
                
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    self._try_update_data()
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    _LOGGER.warning(f"Attempt {attempt + 1}: Error initializing sensor {self._name}: {e}, retrying in {retry_delay}s...")
                    import time
                    time.sleep(retry_delay)
                    self._try_update_data()
                else:
                    _LOGGER.error(f"Final attempt failed for sensor {self._name}: {e}")
        
        _LOGGER.warning(f"All initialization attempts failed for sensor {self._name}, using default value")
        return self._get_default_state()
    
    def _try_update_data(self):
        """Try to update data before retry"""
        try:
            if self._sensor_grp == SENSOR_TYPE_BAT:
                self._data_bridge.updateBat()
            elif self._sensor_grp == SENSOR_TYPE_MOTO:
                self._data_bridge.updateMoto()
            elif self._sensor_grp == SENSOR_TYPE_OVERALL:
                self._data_bridge.updateMotoInfo()
            elif self._sensor_grp == SENSOR_TYPE_TRACK:
                self._data_bridge.updateTrackInfo()
                
            import time
            time.sleep(0.5)
            
        except Exception as e:
            _LOGGER.debug(f"Data update failed during retry for {self._name}: {e}")
    
    def _get_default_state(self):
        """Get default state based on sensor type"""
        if self._sensor_grp == SENSOR_TYPE_BAT:
            return 0
        elif self._sensor_grp == SENSOR_TYPE_MOTO:
            return 0
        elif self._sensor_grp == SENSOR_TYPE_POS:
            return 0.0
        elif self._sensor_grp == SENSOR_TYPE_DIST:
            return 0
        elif self._sensor_grp == SENSOR_TYPE_OVERALL:
            return 0
        elif self._sensor_grp == SENSOR_TYPE_TRACK:
            return "N/A"
        else:
            return 0

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def unit_of_measurement(self):
        return self._uom

    @property
    def icon(self):
        return self._icon

    @property
    def state(self):
        return self._state

    @property
    def device_class(self):
        return self._device_class

    @property
    def extra_state_attributes(self):
        if self._sensor_grp == SENSOR_TYPE_MOTO and self._id_name == "isConnected":
            try:
                return {
                    "bmsId": self._data_bridge.dataBat("bmsId") or "N/A",
                    "latitude": self._data_bridge.dataPos("lat") or 0.0,
                    "longitude": self._data_bridge.dataPos("lng") or 0.0,
                    "gsm": self._data_bridge.dataMoto("gsm") or "N/A",
                    "gps": self._data_bridge.dataMoto("gps") or "N/A",
                    "time": self._data_bridge.dataDist("time") or 0,
                    "range": self._data_bridge.dataMoto("estimatedMileage") or 0,
                    "battery": self._data_bridge.dataBat("batteryCharging") or 0,
                    "battery_grade": self._data_bridge.dataBat("gradeBattery") or 0,
                    "centre_ctrl_batt": self._data_bridge.dataMoto("centreCtrlBattery") or 0,
                }
            except Exception as e:
                _LOGGER.warning(f"Error getting extra state attributes for {self._name}: {e}")
                return {}
        return {}

    def update(self):
        try:
            new_state = None
            
            if self._sensor_grp == SENSOR_TYPE_BAT:
                self._data_bridge.updateBat()
                new_state = self._data_bridge.dataBat(self._id_name)
            elif self._sensor_grp == SENSOR_TYPE_MOTO:
                self._data_bridge.updateMoto()
                new_state = self._data_bridge.dataMoto(self._id_name)
            elif self._sensor_grp == SENSOR_TYPE_POS:
                self._data_bridge.updateMoto()
                new_state = self._data_bridge.dataPos(self._id_name)
            elif self._sensor_grp == SENSOR_TYPE_DIST:
                self._data_bridge.updateMoto()
                new_state = self._data_bridge.dataDist(self._id_name)
            elif self._sensor_grp == SENSOR_TYPE_OVERALL:
                self._data_bridge.updateMotoInfo()
                new_state = self._data_bridge.dataOverall(self._id_name)
            elif self._sensor_grp == SENSOR_TYPE_TRACK:
                self._data_bridge.updateTrackInfo()
                new_state = self._data_bridge.dataTrack(self._id_name)
            
            if new_state is not None:
                if self._is_valid_state(new_state):
                    self._state = new_state
                else:
                    _LOGGER.debug(f"State validation failed for {self._name}: {new_state}, keeping current state")
            else:
                _LOGGER.debug(f"No valid data received for {self._name}, keeping current state")
                
        except Exception as e:
            _LOGGER.warning(f"Error updating sensor {self._name}: {e}")
    
    def _is_valid_state(self, state):
        """Validate if the new state value is reasonable"""
        try:
            if state is None:
                return False
            
            if state == "":
                if self._id_name in ["gradeBattery", "bmsId"]:
                    return True
                return False
            
            if self._sensor_grp == SENSOR_TYPE_BAT:
                if isinstance(state, (int, float)):
                    if self._id_name == "batteryCharging" and 0 <= state <= 100:
                        return True
                    elif self._id_name == "temperature" and -20 <= state <= 80:
                        return True
                    elif self._id_name == "gradeBattery" and 0 <= state <= 100:
                        return True
                    elif self._id_name in ["chargedTimes", "bmsId"]:
                        return state >= 0
                    else:
                        return True
                elif isinstance(state, str):
                    if self._id_name == "temperatureDesc":
                        valid_descriptions = ["normal", "high", "low", "warning", "error"]
                        return state.lower() in valid_descriptions
                    elif self._id_name == "gradeBattery":
                        try:
                            grade = float(state)
                            return 0 <= grade <= 100
                        except (ValueError, TypeError):
                            return False
                    elif self._id_name == "chargedTimes":
                        try:
                            charged_times = int(state)
                            return charged_times >= 0
                        except (ValueError, TypeError):
                            return False
                    else:
                        return True
                return False
                
            elif self._sensor_grp == SENSOR_TYPE_MOTO:
                if isinstance(state, (int, float)):
                    if self._id_name == "nowSpeed" and 0 <= state <= 100:
                        return True
                    elif self._id_name == "estimatedMileage" and 0 <= state <= 1000:
                        return True
                    elif self._id_name == "leftTime" and 0 <= state <= 24:
                        return True
                    elif self._id_name == "centreCtrlBattery" and 0 <= state <= 100:
                        return True
                    else:
                        return True
                elif isinstance(state, str):
                    if self._id_name == "isConnected":
                        return state.lower() in ["true", "false", "1", "0", "connected", "disconnected"]
                    elif self._id_name == "isCharging":
                        return state.lower() in ["true", "false", "1", "0", "charging", "not_charging"]
                    elif self._id_name == "lockStatus":
                        return True
                    else:
                        return True
                return False
                
            elif self._sensor_grp == SENSOR_TYPE_POS:
                if isinstance(state, (int, float)):
                    if self._id_name in ["lat", "lng"]:
                        return -180 <= state <= 180
                    return True
                elif isinstance(state, str):
                    try:
                        pos_value = float(state)
                        if self._id_name in ["lat", "lng"]:
                            return -180 <= pos_value <= 180
                        return True
                    except (ValueError, TypeError):
                        return False
                return False
                
            elif self._sensor_grp == SENSOR_TYPE_DIST:
                if isinstance(state, (int, float)):
                    return state >= 0
                elif isinstance(state, str):
                    try:
                        dist_value = float(state)
                        return dist_value >= 0
                    except (ValueError, TypeError):
                        return False
                return False
                
            elif self._sensor_grp == SENSOR_TYPE_OVERALL:
                if isinstance(state, (int, float)):
                    return state >= 0
                elif isinstance(state, str):
                    try:
                        overall_value = float(state)
                        return overall_value >= 0
                    except (ValueError, TypeError):
                        return state != ""
                return False
                
            elif self._sensor_grp == SENSOR_TYPE_TRACK:
                if isinstance(state, str):
                    return True
                elif isinstance(state, (int, float)):
                    if self._id_name in ["distance", "avespeed", "ridingtime"]:
                        return state >= 0
                    return True
                return False
            
            return True
            
        except Exception as e:
            _LOGGER.debug(f"Error validating state {state} for {self._name}: {e}")
            return False
