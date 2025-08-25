"""API client for NIU integration."""

import hashlib
import json
import logging
from typing import Any

import requests

from .const import (
    ACCOUNT_BASE_URL,
    LOGIN_URI,
    API_BASE_URL,
    MOTOR_BATTERY_API_URI,
    MOTOR_INDEX_API_URI,
    MOTOINFO_LIST_API_URI,
    MOTOINFO_ALL_API_URI,
    TRACK_LIST_API_URI,
)

_LOGGER = logging.getLogger(__name__)


class NiuAuthError(Exception):
    """Exception raised for authentication errors."""


class NiuConnectionError(Exception):
    """Exception raised for connection errors."""


class NiuAPI:
    """NIU API client."""

    def __init__(self, username: str, password: str):
        """Initialize the API client."""
        self.username = username
        self.password = password
        self._token = None

    def get_token(self) -> str:
        """Get authentication token."""
        url = ACCOUNT_BASE_URL + LOGIN_URI
        md5 = hashlib.md5(self.password.encode("utf-8")).hexdigest()
        data = {
            "account": self.username,
            "password": md5,
            "grant_type": "password",
            "scope": "base",
            "app_id": "niu_ktdrr960",
        }
        
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            data = json.loads(response.content.decode())
            
            if "data" not in data or "token" not in data["data"]:
                raise NiuAuthError("Invalid response format")
                
            self._token = data["data"]["token"]["access_token"]
            return self._token
            
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"Failed to connect to NIU API: {err}")
        except (json.JSONDecodeError, KeyError) as err:
            raise NiuAuthError(f"Failed to parse authentication response: {err}")

    def get_vehicles_info(self, token: str) -> dict[str, Any]:
        """Get vehicles information."""
        url = API_BASE_URL + MOTOINFO_LIST_API_URI
        headers = {"token": token}
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return json.loads(response.content.decode())
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"Failed to get vehicles info: {err}")
        except json.JSONDecodeError as err:
            raise NiuConnectionError(f"Failed to parse vehicles response: {err}")

    def get_battery_info(self, sn: str, token: str) -> dict[str, Any]:
        """Get battery information."""
        url = API_BASE_URL + MOTOR_BATTERY_API_URI
        params = {"sn": sn}
        headers = {
            "token": token,
            "user-agent": "manager/4.6.48 (android; IN2020 11);lang=zh-CN;clientIdentifier=Domestic;timezone=Asia/Shanghai;model=IN2020;deviceName=IN2020;ostype=android",
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = json.loads(response.content.decode())
            
            if data.get("status") != 0:
                raise NiuConnectionError(f"API error: {data.get('message', 'Unknown error')}")
                
            return data
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"Failed to get battery info: {err}")
        except json.JSONDecodeError as err:
            raise NiuConnectionError(f"Failed to parse battery response: {err}")

    def get_motor_info(self, sn: str, token: str) -> dict[str, Any]:
        """Get motor information."""
        url = API_BASE_URL + MOTOR_INDEX_API_URI
        params = {"sn": sn}
        headers = {
            "token": token,
            "user-agent": "manager/4.6.48 (android; IN2020 11);lang=zh-CN;clientIdentifier=Domestic;timezone=Asia/Shanghai;model=IN2020;deviceName=IN2020;ostype=android",
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = json.loads(response.content.decode())
            
            if data.get("status") != 0:
                raise NiuConnectionError(f"API error: {data.get('message', 'Unknown error')}")
                
            return data
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"Failed to get motor info: {err}")
        except json.JSONDecodeError as err:
            raise NiuConnectionError(f"Failed to parse motor response: {err}")

    def get_overall_info(self, sn: str, token: str) -> dict[str, Any]:
        """Get overall information."""
        url = API_BASE_URL + MOTOINFO_ALL_API_URI
        headers = {
            "token": token,
            "Accept-Language": "en-US",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url, 
                headers=headers, 
                json={"sn": sn},
                timeout=30
            )
            response.raise_for_status()
            data = json.loads(response.content.decode())
            
            if data.get("status") != 0:
                raise NiuConnectionError(f"API error: {data.get('message', 'Unknown error')}")
                
            return data
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"Failed to get overall info: {err}")
        except json.JSONDecodeError as err:
            raise NiuConnectionError(f"Failed to parse overall response: {err}")

    def get_track_info(self, sn: str, token: str) -> dict[str, Any]:
        """Get track information."""
        url = API_BASE_URL + TRACK_LIST_API_URI
        headers = {
            "token": token,
            "Accept-Language": "en-US",
            "User-Agent": "manager/1.0.0 (identifier);clientIdentifier=identifier",
        }
        
        try:
            response = requests.post(
                url,
                headers=headers,
                json={"index": "0", "pagesize": 10, "sn": sn},
                timeout=30
            )
            response.raise_for_status()
            data = json.loads(response.content.decode())
            
            if data.get("status") != 0:
                raise NiuConnectionError(f"API error: {data.get('message', 'Unknown error')}")
                
            return data
        except requests.exceptions.RequestException as err:
            raise NiuConnectionError(f"Failed to get track info: {err}")
        except json.JSONDecodeError as err:
            raise NiuConnectionError(f"Failed to parse track response: {err}")
