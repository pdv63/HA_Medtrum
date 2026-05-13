"""
Medtrum CGM Integration for Home Assistant
With Config Flow for proper UI setup
FIXED: coordinator storage
"""

import asyncio
import aiohttp
import logging
from datetime import timedelta
from typing import Optional
import json
import base64

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "medtrum"
PLATFORMS = [Platform.SENSOR]
DEFAULT_SCAN_INTERVAL = 5  # minutes


class MedtrumCoordinator(DataUpdateCoordinator):
    """Update coordinator for Medtrum CGM data"""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name="Medtrum CGM",
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        self.config_entry = config_entry
        self.email = config_entry.data.get(CONF_EMAIL)
        self.password = config_entry.data.get(CONF_PASSWORD)
        self.uid = config_entry.data.get("uid")
        self.session_cookies = config_entry.data.get("session_cookies", [])
        self.data = {}

    async def _async_update_data(self):
        """Fetch glucose data"""
        if not self.uid:
            _LOGGER.warning("No UID configured")
            return {}

        try:
            # Build param
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            start_ts = int(datetime(now.year, now.month, now.day, tzinfo=timezone.utc).timestamp())
            end_ts = int(now.timestamp()) + 86400

            param = {"ts": [start_ts, end_ts], "tz": 2}
            param_b64 = base64.b64encode(json.dumps(param).encode()).decode()
            param_encoded = param_b64.replace('+', '%2B').replace('/', '%2F').replace('=', '%3D')

            url = f"https://easyview.medtrum.eu/api/v2.1/monitor/{self.uid}/status?param={param_encoded}"

            # Get cookies from config entry
            stored_cookies = self.config_entry.data.get("session_cookies", [])
            cookie_header = "; ".join(stored_cookies) if stored_cookies else ""

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers={"Cookie": cookie_header} if cookie_header else {},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Failed to fetch glucose data: {resp.status}")

                    data = await resp.json()
                    _LOGGER.debug(f"Glucose data: {data}")

                    if data.get("error") != 0:
                        raise UpdateFailed(f"API error: {data.get('error')}")

                    sensor_status = data.get("data", {}).get("sensor_status", {})
                    pump_status = data.get("data", {}).get("pump_status", {})

                    self.data = {
                        "glucose": sensor_status.get("glucose"),
                        "glucose_unit": "mmol/L",
                        "glucose_rate": sensor_status.get("glucoseRate", 0),
                        "sensor_battery": sensor_status.get("batteryPercent", 0) * 100,
                        "pump_battery": pump_status.get("remainingDose"),
                        "iob": pump_status.get("iob"),
                        "bolus_delivered": pump_status.get("bolusDeliveried"),
                        "connected": pump_status.get("connectState") == 3,
                        "timestamp": now,
                    }

                    _LOGGER.info(
                        f"✅ Glucose: {self.data['glucose']} {self.data['glucose_unit']}, "
                        f"Sensor: {self.data['sensor_battery']:.0f}%, "
                        f"Connected: {self.data['connected']}"
                    )

                    return self.data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Medtrum from config entry"""
    coordinator = MedtrumCoordinator(hass, entry)
    
    # Store coordinator object properly
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # First refresh to get initial data
    await coordinator.async_config_entry_first_refresh()

    # Use hass.async_create_task to avoid blocking call
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Medtrum config entry"""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
