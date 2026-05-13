"""
Medtrum Config Flow for Home Assistant
Proper setup flow with email, password, and 2FA verification
WITH RECONFIGURE support
"""

from typing import Any, Dict, Optional
import voluptuous as vol
import logging

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.update_coordinator import UpdateFailed
import aiohttp

_LOGGER = logging.getLogger(__name__)

DOMAIN = "medtrum"


class MedtrumConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Medtrum."""

    VERSION = 1

    def __init__(self):
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.mfa_email: Optional[str] = None
        self.session_cookies: list = []
        self.reconfig_entry: Optional[config_entries.ConfigEntry] = None

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step - Email & Password"""
        errors = {}

        if user_input is not None:
            self.email = user_input["email"]
            self.password = user_input["password"]

            # Try initial login
            try:
                result = await self._login(self.email, self.password)
                
                if result.get("mfa_required"):
                    self.mfa_email = result.get("mfa_email")
                    _LOGGER.info(f"2FA code sent to {self.mfa_email}")
                    # Go to 2FA step
                    return await self.async_step_mfa()
                else:
                    errors["base"] = "invalid_auth"
            except UpdateFailed as err:
                _LOGGER.error(f"Login error: {err}")
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error(f"Unexpected error: {err}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle reconfigure step"""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        
        if config_entry is None:
            return self.async_abort(reason="reconfigure_failed")

        self.reconfig_entry = config_entry
        self.email = config_entry.data.get("email")
        self.password = config_entry.data.get("password")

        return await self.async_step_user(user_input)

    async def async_step_mfa(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle 2FA verification step"""
        errors = {}

        if user_input is not None:
            mfa_code = user_input["mfa_code"]

            try:
                result = await self._verify_mfa(self.email, self.password, mfa_code)
                
                if result.get("success"):
                    uid = result.get("uid")
                    cookies = result.get("cookies", [])
                    
                    _LOGGER.info(f"✅ 2FA verified! UID: {uid}, Cookies: {cookies}")
                    
                    data = {
                        "email": self.email,
                        "password": self.password,
                        "uid": uid,
                        "session_cookies": cookies,
                    }
                    
                    # If reconfiguring, update existing entry
                    if self.reconfig_entry:
                        self.hass.config_entries.async_update_entry(
                            self.reconfig_entry,
                            data=data
                        )
                        await self.hass.config_entries.async_reload(self.reconfig_entry.entry_id)
                        return self.async_abort(reason="reconfigure_successful")
                    else:
                        # Create new config entry
                        return self.async_create_entry(
                            title=f"Medtrum ({self.email})",
                            data=data,
                        )
                else:
                    errors["base"] = "invalid_mfa"
                    
            except UpdateFailed as err:
                _LOGGER.error(f"MFA error: {err}")
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.error(f"Unexpected error: {err}")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema(
                {
                    vol.Required("mfa_code"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "email": self.mfa_email or self.email,
            },
        )

    async def _login(self, email: str, password: str) -> Dict[str, Any]:
        """Perform login and check for MFA requirement"""
        try:
            async with aiohttp.ClientSession() as session:
                body = {
                    "user_name": email,
                    "user_type": "P",
                    "password": password
                }

                async with session.post(
                    "https://easyview.medtrum.eu/v3/api/v2.0/login",
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"Login failed: {resp.status}")

                    data = await resp.json()

                    if data.get("error") == 63 and data.get("mfa") == "Y":
                        # Request 2FA code
                        mfa_body = {
                            "user_name": email,
                            "flag": "email",
                            "country": "GB",
                            "purpose": "login_mfa"
                        }

                        async with session.post(
                            "https://easyview.medtrum.eu/api/v2.0/seccode/send",
                            json=mfa_body,
                            timeout=aiohttp.ClientTimeout(total=30),
                        ) as mfa_resp:
                            if mfa_resp.status == 200:
                                mfa_data = await mfa_resp.json()
                                if mfa_data.get("error") == 0:
                                    return {
                                        "mfa_required": True,
                                        "mfa_email": data.get("mfa_email", {}).get("email"),
                            }

                        raise UpdateFailed("Failed to request 2FA code")
                    else:
                        raise UpdateFailed(f"Unexpected response: {data}")

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}")

    async def _verify_mfa(self, email: str, password: str, mfa_code: str) -> Dict[str, Any]:
        """Verify 2FA code and complete authentication"""
        try:
            async with aiohttp.ClientSession() as session:
                body = {
                    "user_name": email,
                    "user_type": "P",
                    "password": password,
                    "mfa_seccode": mfa_code
                }

                async with session.post(
                    "https://easyview.medtrum.eu/v3/api/v2.0/login",
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        raise UpdateFailed(f"MFA verification failed: {resp.status}")

                    data = await resp.json()

                    if data.get("error") == 0 and data.get("uid"):
                        # Extract and store cookies
                        cookies = []
                        if "set-cookie" in resp.headers:
                            cookie_list = resp.headers.getall("set-cookie", [])
                            cookies = [c.split(';')[0] for c in cookie_list]
                        
                        _LOGGER.debug(f"Cookies extracted: {cookies}")
                        
                        return {
                            "success": True,
                            "uid": data.get("uid"),
                            "cookies": cookies,
                        }
                    else:
                        raise UpdateFailed(f"MFA verification failed: {data}")

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow"""
        return MedtrumOptionsFlow(config_entry)


class MedtrumOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Medtrum"""

    def __init__(self, config_entry: config_entries.ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle options step"""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "scan_interval",
                        default=self.config_entry.options.get("scan_interval", 5),
                    ): int,
                }
            ),
        )
