"""Data coordinator for NIU integration."""

import logging
from datetime import datetime, timedelta
from time import gmtime, strftime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import NiuAPI, NiuAuthError, NiuConnectionError
from .const import (
    SENSOR_TYPE_BAT,
    SENSOR_TYPE_MOTO,
    SENSOR_TYPE_DIST,
    SENSOR_TYPE_OVERALL,
    SENSOR_TYPE_POS,
    SENSOR_TYPE_TRACK,
)

_LOGGER = logging.getLogger(__name__)


class NiuDataCoordinator(DataUpdateCoordinator):
    """NIU data coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="NIU Scooter",
            update_interval=timedelta(seconds=30),
        )
        
        self.config_entry = config_entry
        self.api = NiuAPI(
            config_entry.data["username"],
            config_entry.data["password"]
        )
        self.sn = None
        self.token = None
        self._data_bat = None
        self._data_moto = None
        self._data_moto_info = None
        self._data_track_info = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from NIU API."""
        try:
            # Get token if not available
            if not self.token:
                self.token = await self.hass.async_add_executor_job(self.api.get_token)
                
                # Get SN from vehicles info
                vehicles = await self.hass.async_add_executor_job(
                    self.api.get_vehicles_info, self.token
                )
                scooter_id = self.config_entry.data.get("scooter_id", 0)
                self.sn = vehicles["data"]["items"][scooter_id]["sn_id"]

            # Update all data
            await self._update_battery_info()
            await self._update_motor_info()
            await self._update_overall_info()
            await self._update_track_info()

            return {
                "battery": self._data_bat,
                "motor": self._data_moto,
                "overall": self._data_moto_info,
                "track": self._data_track_info,
            }

        except (NiuAuthError, NiuConnectionError) as err:
            _LOGGER.error("Failed to update NIU data: %s", err)
            # Reset token on auth error
            if isinstance(err, NiuAuthError):
                self.token = None
            raise

    async def _update_battery_info(self):
        """Update battery information."""
        try:
            self._data_bat = await self.hass.async_add_executor_job(
                self.api.get_battery_info, self.sn, self.token
            )
        except Exception as err:
            _LOGGER.warning("Failed to update battery info: %s", err)

    async def _update_motor_info(self):
        """Update motor information."""
        try:
            self._data_moto = await self.hass.async_add_executor_job(
                self.api.get_motor_info, self.sn, self.token
            )
        except Exception as err:
            _LOGGER.warning("Failed to update motor info: %s", err)

    async def _update_overall_info(self):
        """Update overall information."""
        try:
            self._data_moto_info = await self.hass.async_add_executor_job(
                self.api.get_overall_info, self.sn, self.token
            )
        except Exception as err:
            _LOGGER.warning("Failed to update overall info: %s", err)

    async def _update_track_info(self):
        """Update track information."""
        try:
            self._data_track_info = await self.hass.async_add_executor_job(
                self.api.get_track_info, self.sn, self.token
            )
        except Exception as err:
            _LOGGER.warning("Failed to update track info: %s", err)

    def get_battery_data(self, field: str) -> Any:
        """Get battery data by field."""
        if not self._data_bat or "data" not in self._data_bat:
            return None
        return self._data_bat["data"]["batteries"]["compartmentA"].get(field)

    def get_motor_data(self, field: str) -> Any:
        """Get motor data by field."""
        if not self._data_moto or "data" not in self._data_moto:
            return None
        return self._data_moto["data"].get(field)

    def get_distance_data(self, field: str) -> Any:
        """Get distance data by field."""
        if not self._data_moto or "data" not in self._data_moto or "lastTrack" not in self._data_moto["data"]:
            return None
        return self._data_moto["data"]["lastTrack"].get(field)

    def get_position_data(self, field: str) -> Any:
        """Get position data by field."""
        if not self._data_moto or "data" not in self._data_moto or "postion" not in self._data_moto["data"]:
            return None
        return self._data_moto["data"]["postion"].get(field)

    def get_overall_data(self, field: str) -> Any:
        """Get overall data by field."""
        if not self._data_moto_info or "data" not in self._data_moto_info:
            return None
        return self._data_moto_info["data"].get(field)

    def get_track_data(self, field: str) -> Any:
        """Get track data by field."""
        if not self._data_track_info or "data" not in self._data_track_info or not self._data_track_info["data"]:
            return None
            
        if field == "startTime" or field == "endTime":
            return datetime.fromtimestamp(
                (self._data_track_info["data"][0][field]) / 1000
            ).strftime("%Y-%m-%d %H:%M:%S")
        if field == "ridingtime":
            return strftime(
                "%H:%M:%S", gmtime(self._data_track_info["data"][0][field])
            )
        if field == "track_thumb":
            thumburl = self._data_track_info["data"][0][field].replace(
                "app-api.niucache.com", "app-api.niu.com"
            )
            return thumburl
        return self._data_track_info["data"][0].get(field)

    def get_data_by_type(self, sensor_type: str, field: str) -> Any:
        """Get data by sensor type and field."""
        if sensor_type == SENSOR_TYPE_BAT:
            return self.get_battery_data(field)
        elif sensor_type == SENSOR_TYPE_MOTO:
            return self.get_motor_data(field)
        elif sensor_type == SENSOR_TYPE_DIST:
            return self.get_distance_data(field)
        elif sensor_type == SENSOR_TYPE_POS:
            return self.get_position_data(field)
        elif sensor_type == SENSOR_TYPE_OVERALL:
            return self.get_overall_data(field)
        elif sensor_type == SENSOR_TYPE_TRACK:
            return self.get_track_data(field)
        return None
