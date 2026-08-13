"""Config flow for Trakt."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.config_entry_oauth2_flow import AbstractOAuth2FlowHandler

from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from .defaults import SENSOR_GROUPS


class OAuth2FlowHandler(AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Config flow to handle Trakt OAuth2 authentication."""

    VERSION = 1
    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    _reauth_entry: ConfigEntry | None = None

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "OptionsFlowHandler":
        """Return the options flow for this integration."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow started by a user."""
        if user_input:
            self.user_input = user_input
            await self.async_set_unique_id(user_input[CONF_CLIENT_ID])
            self._abort_if_unique_id_configured()

            self.config = user_input

            OAuth2FlowHandler.async_register_implementation(
                self.hass,
                config_entry_oauth2_flow.LocalOAuth2Implementation(
                    self.hass,
                    DOMAIN,
                    user_input[CONF_CLIENT_ID],
                    user_input[CONF_CLIENT_SECRET],
                    OAUTH2_AUTHORIZE,
                    OAUTH2_TOKEN,
                ),
            )

            return await self.async_step_pick_implementation()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                }
            ),
        )

    async def async_step_reauth(self, entry_data: dict) -> FlowResult:
        """Perform reauth after Trakt rejects the stored token."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None) -> FlowResult:
        """Ask for confirmation, then restart the OAuth dance with stored credentials."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )

        entry = self._reauth_entry
        self.user_input = {
            CONF_CLIENT_ID: entry.data[CONF_CLIENT_ID],
            CONF_CLIENT_SECRET: entry.data[CONF_CLIENT_SECRET],
        }

        OAuth2FlowHandler.async_register_implementation(
            self.hass,
            config_entry_oauth2_flow.LocalOAuth2Implementation(
                self.hass,
                DOMAIN,
                entry.data[CONF_CLIENT_ID],
                entry.data[CONF_CLIENT_SECRET],
                OAUTH2_AUTHORIZE,
                OAUTH2_TOKEN,
            ),
        )

        return await self.async_step_pick_implementation()

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """
        Create an entry for the flow.

        Ok to override if you want to fetch extra info or even add another step.
        """
        augmented_data = {**data, **self.user_input}

        if self._reauth_entry is not None:
            self.hass.config_entries.async_update_entry(
                self._reauth_entry, data=augmented_data
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._reauth_entry.entry_id)
            )
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(title="Trakt", data=augmented_data)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for the Trakt integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Store the entry being configured."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        """Manage the integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options or {}
        schema = vol.Schema(
            {
                vol.Required(
                    f"enable_{group}",
                    default=current.get(f"enable_{group}", True),
                ): bool
                for group in SENSOR_GROUPS
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
