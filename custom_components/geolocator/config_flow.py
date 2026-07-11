import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_PROVIDER,
    CONF_USER_AGENT,
    CONF_MAX_REQUESTS_PER_SECOND,
    CONF_MAX_REQUESTS_PER_DAY,
    API_PROVIDER_META,
    DEFAULT_OSM_USER_AGENT,
)

_LOGGER = logging.getLogger(__name__)

OSM_POLICY_NOTICE = (
    "OpenStreetMap Nominatim usage policy applies: requests are capped at 1/second, "
    "you must supply a valid User-Agent that identifies this installation, and results "
    "are © OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright). "
    "Full policy: https://operations.osmfoundation.org/policies/nominatim/"
)


def _provider_label(meta: dict) -> str:
    if meta.get("needs_user_agent"):
        return f"{meta['name']} (User-Agent required)"
    if not meta.get("needs_key"):
        return f"{meta['name']} (no key required)"
    return meta["name"]


def _provider_notice(provider: str) -> str:
    return OSM_POLICY_NOTICE if provider == "osm" else ""


class GeoLocatorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._errors = {}
        self._selected_provider = None

    async def async_step_user(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            self._selected_provider = user_input[CONF_API_PROVIDER]
            return await self.async_step_credentials()

        provider_options = {
            k: _provider_label(v) for k, v in API_PROVIDER_META.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_PROVIDER): vol.In(provider_options)
            }),
            errors=self._errors,
        )

    async def async_step_credentials(self, user_input=None):
        self._errors = {}

        provider = self._selected_provider
        provider_meta = API_PROVIDER_META.get(provider, {})

        if user_input is not None:
            return self.async_create_entry(
                title="GeoLocator",
                data={
                    CONF_API_PROVIDER: provider,
                    CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                    CONF_USER_AGENT: user_input.get(CONF_USER_AGENT, ""),
                    CONF_MAX_REQUESTS_PER_SECOND: user_input.get(CONF_MAX_REQUESTS_PER_SECOND, 0.0),
                    CONF_MAX_REQUESTS_PER_DAY: user_input.get(CONF_MAX_REQUESTS_PER_DAY, 0),
                }
            )

        if provider == "offline":
            return self.async_create_entry(
                title="GeoLocator",
                data={
                    CONF_API_PROVIDER: provider,
                    CONF_API_KEY: "",
                    CONF_USER_AGENT: "",
                    CONF_MAX_REQUESTS_PER_SECOND: 0.0,
                    CONF_MAX_REQUESTS_PER_DAY: 0,
                }
            )

        schema_dict = {}
        if provider_meta.get("needs_key"):
            schema_dict[vol.Required(CONF_API_KEY)] = str
        if provider_meta.get("needs_user_agent"):
            schema_dict[vol.Required(CONF_USER_AGENT, default=DEFAULT_OSM_USER_AGENT)] = str

        schema_dict[vol.Optional(CONF_MAX_REQUESTS_PER_SECOND, default=0.0)] = vol.Coerce(float)
        schema_dict[vol.Optional(CONF_MAX_REQUESTS_PER_DAY, default=0)] = vol.Coerce(int)

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema(schema_dict),
            errors=self._errors,
            description_placeholders={"provider_notice": _provider_notice(provider)}
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GeoLocatorOptionsFlowHandler(config_entry)


class GeoLocatorOptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):
    def __init__(self, config_entry):
        super().__init__(config_entry)
        self._errors = {}
        self._selected_provider = None

    async def async_step_init(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            self._selected_provider = user_input[CONF_API_PROVIDER]
            return await self.async_step_options_credentials()

        provider_options = {
            k: _provider_label(v) for k, v in API_PROVIDER_META.items()
        }

        current_provider = self.config_entry.options.get(
            CONF_API_PROVIDER,
            self.config_entry.data.get(CONF_API_PROVIDER)
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_API_PROVIDER, default=current_provider): vol.In(provider_options)
            }),
            errors=self._errors,
            description_placeholders={}
        )

    async def async_step_options_credentials(self, user_input=None):
        self._errors = {}

        provider = self._selected_provider
        provider_meta = API_PROVIDER_META.get(provider, {})

        current_key = self.config_entry.options.get(
            CONF_API_KEY,
            self.config_entry.data.get(CONF_API_KEY, "")
        )
        current_user_agent = self.config_entry.options.get(
            CONF_USER_AGENT,
            self.config_entry.data.get(CONF_USER_AGENT, "") or DEFAULT_OSM_USER_AGENT
        )
        current_max_requests_per_second = self.config_entry.options.get(
            CONF_MAX_REQUESTS_PER_SECOND,
            self.config_entry.data.get(CONF_MAX_REQUESTS_PER_SECOND, 0.0)
        )
        current_max_requests_per_day = self.config_entry.options.get(
            CONF_MAX_REQUESTS_PER_DAY,
            self.config_entry.data.get(CONF_MAX_REQUESTS_PER_DAY, 0)
        )

        if provider == "offline":
            return self.async_create_entry(
                title="",
                data={
                    CONF_API_PROVIDER: provider,
                    CONF_API_KEY: "",
                    CONF_USER_AGENT: "",
                    CONF_MAX_REQUESTS_PER_SECOND: 0.0,
                    CONF_MAX_REQUESTS_PER_DAY: 0,
                }
            )

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_API_PROVIDER: provider,
                    CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                    CONF_USER_AGENT: user_input.get(CONF_USER_AGENT, ""),
                    CONF_MAX_REQUESTS_PER_SECOND: user_input.get(CONF_MAX_REQUESTS_PER_SECOND, 0.0),
                    CONF_MAX_REQUESTS_PER_DAY: user_input.get(CONF_MAX_REQUESTS_PER_DAY, 0),
                }
            )

        schema_dict = {}
        if provider_meta.get("needs_key"):
            schema_dict[vol.Required(CONF_API_KEY, default=current_key)] = str
        if provider_meta.get("needs_user_agent"):
            schema_dict[vol.Required(CONF_USER_AGENT, default=current_user_agent)] = str

        schema_dict[vol.Optional(CONF_MAX_REQUESTS_PER_SECOND, default=current_max_requests_per_second)] = vol.Coerce(float)
        schema_dict[vol.Optional(CONF_MAX_REQUESTS_PER_DAY, default=current_max_requests_per_day)] = vol.Coerce(int)

        return self.async_show_form(
            step_id="options_credentials",
            data_schema=vol.Schema(schema_dict),
            errors=self._errors,
            description_placeholders={"provider_notice": _provider_notice(provider)}
        )
