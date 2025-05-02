from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN, API_PROVIDERS

_LOGGER = logging.getLogger(__name__)


REQUIRES_KEY = {"google", "geonames"}

class GeoLocatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.selected_provider: str | None = None

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self.selected_provider = user_input["api_provider"]
            if self.selected_provider in REQUIRES_KEY:
                return await self.async_step_api_key()
            return self.async_create_entry(
                title="GeoLocator",
                data={
                    "api_provider": self.selected_provider,
                    "api_key": "",
                },
            )

        schema = vol.Schema({
            vol.Required("api_provider", default="offline"): vol.In(list(API_PROVIDERS.keys())),
        })

        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_api_key(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="GeoLocator",
                data={
                    "api_provider": self.selected_provider,
                    "api_key": user_input["api_key"],
                },
            )

        schema = vol.Schema({
            vol.Required("api_key"): str,
        })

        return self.async_show_form(step_id="api_key", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GeoLocatorOptionsFlowHandler(config_entry)


class GeoLocatorOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        self._config_entry = config_entry
        self._selected_provider = config_entry.options.get("api_provider") or config_entry.data.get("api_provider", "offline")

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self._selected_provider = user_input["api_provider"]
            if self._selected_provider in REQUIRES_KEY:
                return await self.async_step_api_key()
            return self.async_create_entry(
                title="GeoLocator",
                data={
                    "api_provider": self._selected_provider,
                    "api_key": "",
                },
            )

        schema = vol.Schema({
            vol.Required("api_provider", default="offline"): vol.In(list(API_PROVIDERS.keys())),
        })

        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_api_key(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="GeoLocator",
                data={
                    "api_provider": self._selected_provider,
                    "api_key": user_input["api_key"],
                },
            )

        schema = vol.Schema({
            vol.Required("api_key", default=self._config_entry.options.get("api_key", "")): str,
        })

        return self.async_show_form(step_id="api_key", data_schema=schema)
