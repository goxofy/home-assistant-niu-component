"""Support for NIU Scooters sensors."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    AVAILABLE_SENSORS,
    CONF_MONITORED_VARIABLES,
    CONF_SCOOTER_ID,
    DEFAULT_MONITORED_VARIABLES,
    DOMAIN,
    SENSOR_TYPE_BAT,
    SENSOR_TYPE_MOTO,
    SENSOR_TYPE_DIST,
    SENSOR_TYPE_OVERALL,
    SENSOR_TYPE_POS,
    SENSOR_TYPE_TRACK,
)
from .coordinator import NiuDataCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    "BatteryCharge": [
        "battery_charge",
        "%",
        "batteryCharging",
        SENSOR_TYPE_BAT,
        SensorDeviceClass.BATTERY,
        "mdi:battery-charging-50",
        SensorStateClass.MEASUREMENT,
    ],
    "Isconnected": [
        "is_connected",
        "",
        "isConnected",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:connection",
        None,
    ],
    "TimesCharged": [
        "times_charged",
        "x",
        "chargedTimes",
        SENSOR_TYPE_BAT,
        None,
        "mdi:battery-charging-wireless",
        SensorStateClass.TOTAL,
    ],
    "temperatureDesc": [
        "temp_descr",
        "",
        "temperatureDesc",
        SENSOR_TYPE_BAT,
        None,
        "mdi:thermometer-alert",
        None,
    ],
    "Temperature": [
        "temperature",
        "°C",
        "temperature",
        SENSOR_TYPE_BAT,
        SensorDeviceClass.TEMPERATURE,
        "mdi:thermometer",
        SensorStateClass.MEASUREMENT,
    ],
    "BatteryGrade": [
        "battery_grade",
        "%",
        "gradeBattery",
        SENSOR_TYPE_BAT,
        SensorDeviceClass.BATTERY,
        "mdi:car-battery",
        SensorStateClass.MEASUREMENT,
    ],
    "CurrentSpeed": [
        "current_speed",
        "km/h",
        "nowSpeed",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:speedometer",
        SensorStateClass.MEASUREMENT,
    ],
    "ScooterConnected": [
        "scooter_connected",
        "",
        "isConnected",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:motorbike-electric",
        None,
    ],
    "IsCharging": [
        "is_charging",
        "",
        "isCharging",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:battery-charging",
        None,
    ],
    "IsLocked": [
        "is_locked",
        "",
        "lockStatus",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:lock",
        None,
    ],
    "TimeLeft": [
        "time_left",
        "h",
        "leftTime",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:av-timer",
        SensorStateClass.MEASUREMENT,
    ],
    "EstimatedMileage": [
        "estimated_mileage",
        "km",
        "estimatedMileage",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:map-marker-distance",
        SensorStateClass.MEASUREMENT,
    ],
    "centreCtrlBatt": [
        "centre_ctrl_batt",
        "%",
        "centreCtrlBattery",
        SENSOR_TYPE_MOTO,
        SensorDeviceClass.BATTERY,
        "mdi:car-cruise-control",
        SensorStateClass.MEASUREMENT,
    ],
    "HDOP": [
        "hdp",
        "",
        "hdop",
        SENSOR_TYPE_MOTO,
        None,
        "mdi:map-marker",
        SensorStateClass.MEASUREMENT,
    ],
    "Longitude": [
        "long",
        "",
        "lng",
        SENSOR_TYPE_POS,
        None,
        "mdi:map-marker",
        SensorStateClass.MEASUREMENT,
    ],
    "Latitude": [
        "lat",
        "",
        "lat",
        SENSOR_TYPE_POS,
        None,
        "mdi:map-marker",
        SensorStateClass.MEASUREMENT,
    ],
    "Distance": [
        "distance",
        "m",
        "distance",
        SENSOR_TYPE_DIST,
        None,
        "mdi:map-marker-distance",
        SensorStateClass.MEASUREMENT,
    ],
    "RidingTime": [
        "riding_time",
        "s",
        "ridingTime",
        SENSOR_TYPE_DIST,
        None,
        "mdi:map-clock",
        SensorStateClass.MEASUREMENT,
    ],
    "totalMileage": [
        "total_mileage",
        "km",
        "totalMileage",
        SENSOR_TYPE_OVERALL,
        None,
        "mdi:map-marker-distance",
        SensorStateClass.TOTAL,
    ],
    "DaysInUse": [
        "bind_days_count",
        "days",
        "bindDaysCount",
        SENSOR_TYPE_OVERALL,
        None,
        "mdi:calendar-today",
        SensorStateClass.TOTAL,
    ],
    "LastTrackStartTime": [
        "last_track_start_time",
        "",
        "startTime",
        SENSOR_TYPE_TRACK,
        None,
        "mdi:clock-start",
        None,
    ],
    "LastTrackEndTime": [
        "last_track_end_time",
        "",
        "endTime",
        SENSOR_TYPE_TRACK,
        None,
        "mdi:clock-end",
        None,
    ],
    "LastTrackDistance": [
        "last_track_distance",
        "m",
        "distance",
        SENSOR_TYPE_TRACK,
        None,
        "mdi:map-marker-distance",
        SensorStateClass.MEASUREMENT,
    ],
    "LastTrackAverageSpeed": [
        "last_track_average_speed",
        "km/h",
        "avespeed",
        SENSOR_TYPE_TRACK,
        None,
        "mdi:speedometer",
        SensorStateClass.MEASUREMENT,
    ],
    "LastTrackRidingtime": [
        "last_track_riding_time",
        "",
        "ridingtime",
        SENSOR_TYPE_TRACK,
        None,
        "mdi:timelapse",
        None,
    ],
    "LastTrackThumb": [
        "last_track_thumb",
        "",
        "track_thumb",
        SENSOR_TYPE_TRACK,
        None,
        "mdi:map",
        None,
    ],
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up NIU sensors based on a config entry."""
    coordinator = config_entry.runtime_data.coordinator
    
    # Get monitored variables from config
    monitored_variables = config_entry.data.get(
        CONF_MONITORED_VARIABLES, DEFAULT_MONITORED_VARIABLES
    )
    
    # Get scooter info for device info
    scooter_id = config_entry.data.get(CONF_SCOOTER_ID, 0)
    
    entities = []
    for sensor in monitored_variables:
        if sensor in SENSOR_TYPES:
            sensor_config = SENSOR_TYPES[sensor]
            entities.append(
                NiuSensor(
                    coordinator,
                    sensor,
                    sensor_config[0],
                    sensor_config[1],
                    sensor_config[2],
                    sensor_config[3],
                    sensor_config[4],
                    sensor_config[5],
                    sensor_config[6],
                    config_entry,
                )
            )

    async_add_entities(entities)


class NiuSensor(SensorEntity):
    """Representation of a NIU sensor."""

    def __init__(
        self,
        coordinator: NiuDataCoordinator,
        sensor_name: str,
        sensor_id: str,
        unit_of_measurement: str,
        id_name: str,
        sensor_type: str,
        device_class: SensorDeviceClass | None,
        icon: str,
        state_class: SensorStateClass | None,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._sensor_name = sensor_name
        self._sensor_id = sensor_id
        self._unit_of_measurement = unit_of_measurement
        self._id_name = id_name
        self._sensor_type = sensor_type
        self._device_class = device_class
        self._icon = icon
        self._state_class = state_class
        self._config_entry = config_entry
        
        # Get scooter ID from config
        scooter_id = config_entry.data.get(CONF_SCOOTER_ID, 0)
        
        # Create unique ID with scooter ID
        self._attr_unique_id = f"niu_scooter_{scooter_id}_{sensor_id}"
        self._attr_name = f"NIU Scooter {scooter_id} {sensor_name}"
        
        # Set device info with scooter ID
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"niu_scooter_{scooter_id}_{coordinator.sn}")},
            name=f"NIU Scooter {scooter_id}",
            manufacturer="NIU",
            model="Electric Scooter",
            configuration_url="https://account.niu.com",
        )

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @property
    def icon(self) -> str | None:
        """Return the icon."""
        return self._icon

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the device class."""
        return self._device_class

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the state class."""
        return self._state_class

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
            
        return self.coordinator.get_data_by_type(self._sensor_type, self._id_name)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return entity specific state attributes."""
        if self._sensor_type == SENSOR_TYPE_MOTO and self._id_name == "isConnected":
            try:
                return {
                    "bmsId": self.coordinator.get_battery_data("bmsId") or "N/A",
                    "latitude": self.coordinator.get_position_data("lat") or 0.0,
                    "longitude": self.coordinator.get_position_data("lng") or 0.0,
                    "gsm": self.coordinator.get_motor_data("gsm") or "N/A",
                    "gps": self.coordinator.get_motor_data("gps") or "N/A",
                    "time": self.coordinator.get_distance_data("time") or 0,
                    "range": self.coordinator.get_motor_data("estimatedMileage") or 0,
                    "battery": self.coordinator.get_battery_data("batteryCharging") or 0,
                    "battery_grade": self.coordinator.get_battery_data("gradeBattery") or 0,
                    "centre_ctrl_batt": self.coordinator.get_motor_data("centreCtrlBattery") or 0,
                }
            except Exception as e:
                _LOGGER.warning(f"Error getting extra state attributes for {self._attr_name}: {e}")
                return {}
        return None

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
