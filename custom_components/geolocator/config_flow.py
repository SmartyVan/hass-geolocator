import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import (
    DOMAIN,
    CONF_API_KEY,
    CONF_API_PROVIDER,
    CONF_ELEVATION_SENSOR,
    API_PROVIDER_META,
)

# Optional selector for a sensor whose value tracks the current altitude.
# Restricted to the sensor domain; the device_class filter keeps the picker
# tidy but still allows any sensor to be typed in.
_ELEVATION_SELECTOR = EntitySelector(
    EntitySelectorConfig(domain="sensor", device_class="distance")
)

_LOGGER = logging.getLogger(__name__)


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
            k: f"{v['name']} (no key required)" if not v['needs_key'] else v['name']
            for k, v in API_PROVIDER_META.items()
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
                    CONF_API_KEY: user_input.get(CONF_API_KEY, "")
                }
            )

        if provider_meta.get("needs_key"):
            return self.async_show_form(
                step_id="credentials",
                data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
                errors=self._errors,
                description_placeholders={}
            )
        else:
            # Skip credentials step if not needed
            return self.async_create_entry(
                title="GeoLocator",
                data={CONF_API_PROVIDER: provider, CONF_API_KEY: ""}
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
        self._elevation_sensor = ""

    async def async_step_init(self, user_input=None):
        self._errors = {}

        if user_input is not None:
            self._selected_provider = user_input[CONF_API_PROVIDER]
            self._elevation_sensor = user_input.get(CONF_ELEVATION_SENSOR, "")
            return await self.async_step_options_credentials()

        provider_options = {
            k: f"{v['name']} (no key required)" if not v['needs_key'] else v['name']
            for k, v in API_PROVIDER_META.items()
        }

        current_provider = self.config_entry.options.get(
            CONF_API_PROVIDER,
            self.config_entry.data.get(CONF_API_PROVIDER)
        )
        current_elevation = self.config_entry.options.get(
            CONF_ELEVATION_SENSOR,
            self.config_entry.data.get(CONF_ELEVATION_SENSOR, "")
        )

        schema = {
            vol.Required(CONF_API_PROVIDER, default=current_provider): vol.In(provider_options),
        }
        # Optional: a sensor whose value tracks altitude. Use suggested_value so
        # an empty selection clears it.
        elev_key = vol.Optional(
            CONF_ELEVATION_SENSOR,
            description={"suggested_value": current_elevation} if current_elevation else None,
        )
        schema[elev_key] = _ELEVATION_SELECTOR

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
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

        if not provider_meta.get("needs_key"):
            return self.async_create_entry(
                title="",
                data={
                    CONF_API_PROVIDER: provider,
                    CONF_API_KEY: "",
                    CONF_ELEVATION_SENSOR: self._elevation_sensor,
                }
            )

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    CONF_API_PROVIDER: provider,
                    CONF_API_KEY: user_input.get(CONF_API_KEY, ""),
                    CONF_ELEVATION_SENSOR: self._elevation_sensor,
                }
            )

        return self.async_show_form(
            step_id="options_credentials",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY, default=current_key): str}),
            errors=self._errors,
            description_placeholders={}
        )
