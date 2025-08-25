"""Config flow for NIU integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_MONITORED_VARIABLES,
    CONF_SCOOTER_ID,
    DEFAULT_MONITORED_VARIABLES,
    DEFAULT_SCOOTER_ID,
    DOMAIN,
    AVAILABLE_SENSORS,
)
from .api import NiuAPI, NiuAuthError, NiuConnectionError

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SCOOTER_ID, default=DEFAULT_SCOOTER_ID): int,
    }
)

STEP_SENSORS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_MONITORED_VARIABLES,
            default=DEFAULT_MONITORED_VARIABLES,
        ): list,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = NiuAPI(data[CONF_USERNAME], data[CONF_PASSWORD])
    
    try:
        # Test authentication
        token = await hass.async_add_executor_job(api.get_token)
        if not token:
            raise NiuAuthError("Failed to get authentication token")
        
        # Get vehicles list
        vehicles = await hass.async_add_executor_job(api.get_vehicles_info, token)
        if not vehicles or "data" not in vehicles or "items" not in vehicles["data"]:
            raise NiuConnectionError("Failed to get vehicles information")
        
        scooter_id = data.get(CONF_SCOOTER_ID, DEFAULT_SCOOTER_ID)
        if scooter_id >= len(vehicles["data"]["items"]):
            raise NiuConnectionError(f"Scooter ID {scooter_id} is out of range")
        
        scooter_name = vehicles["data"]["items"][scooter_id]["scooter_name"]
        
        return {
            "title": f"NIU Scooter - {scooter_name}",
            "token": token,
            "scooter_id": scooter_id,
            "scooter_name": scooter_name,
            "sn_id": vehicles["data"]["items"][scooter_id]["sn_id"],
        }
        
    except NiuAuthError as err:
        raise InvalidAuth from err
    except NiuConnectionError as err:
        raise CannotConnect from err
    except Exception as err:
        _LOGGER.exception("Unexpected error during validation")
        raise CannotConnect from err


class NiuConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NIU integration."""

    VERSION = 1
    _input_data: dict[str, Any]

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> NiuOptionsFlowHandler:
        """Get the options flow for this handler."""
        return NiuOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                self._input_data = {**user_input, **info}
                return await self.async_step_sensors()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_sensors(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the sensors selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate sensor selection
            monitored_variables = user_input.get(CONF_MONITORED_VARIABLES, [])
            if not monitored_variables:
                errors["base"] = "no_sensors_selected"
            else:
                # Check if all selected sensors are valid
                invalid_sensors = [s for s in monitored_variables if s not in AVAILABLE_SENSORS]
                if invalid_sensors:
                    errors["base"] = "invalid_sensors"
                else:
                    # Create unique ID based on scooter SN
                    unique_id = f"niu_scooter_{self._input_data['sn_id']}"
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()

                    # Create the config entry
                    config_data = {
                        CONF_USERNAME: self._input_data[CONF_USERNAME],
                        CONF_PASSWORD: self._input_data[CONF_PASSWORD],
                        CONF_SCOOTER_ID: self._input_data[CONF_SCOOTER_ID],
                        CONF_MONITORED_VARIABLES: monitored_variables,
                    }

                    return self.async_create_entry(
                        title=self._input_data["title"], data=config_data
                    )

        return self.async_show_form(
            step_id="sensors", data_schema=STEP_SENSORS_DATA_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfigure step."""
        errors: dict[str, str] = {}
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if user_input is not None:
            try:
                # Keep the same scooter_id and monitored_variables
                user_input[CONF_SCOOTER_ID] = config_entry.data[CONF_SCOOTER_ID]
                user_input[CONF_MONITORED_VARIABLES] = config_entry.data[CONF_MONITORED_VARIABLES]
                
                await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    config_entry,
                    unique_id=config_entry.unique_id,
                    data={**config_entry.data, **user_input},
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=config_entry.data[CONF_USERNAME]
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )


class NiuOptionsFlowHandler(OptionsFlow):
    """Handle NIU options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Validate sensor selection
            monitored_variables = user_input.get(CONF_MONITORED_VARIABLES, [])
            if not monitored_variables:
                errors["base"] = "no_sensors_selected"
            else:
                # Check if all selected sensors are valid
                invalid_sensors = [s for s in monitored_variables if s not in AVAILABLE_SENSORS]
                if invalid_sensors:
                    errors["base"] = "invalid_sensors"
                else:
                    return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_MONITORED_VARIABLES,
                    default=self.config_entry.data.get(
                        CONF_MONITORED_VARIABLES, DEFAULT_MONITORED_VARIABLES
                    ),
                ): list,
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
