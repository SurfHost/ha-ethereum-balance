"""Config flow for the Ethereum Balance integration."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EtherscanClient
from .const import (
    CONF_ADDRESSES,
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import EthereumBalanceConfigEntry
from .errors import EtherscanAuthenticationError, EtherscanConnectionError

_LOGGER = logging.getLogger(__name__)

ETH_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class EthereumBalanceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ethereum Balance."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = EtherscanClient(session, user_input[CONF_API_KEY])

            try:
                await client.async_validate_key()
            except EtherscanAuthenticationError:
                errors["base"] = "invalid_auth"
            except EtherscanConnectionError:
                errors["base"] = "cannot_connect"
            except (TimeoutError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                unique_id = hashlib.sha256(
                    user_input[CONF_API_KEY].encode()
                ).hexdigest()[:8]
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Ethereum Balance",
                    data={CONF_API_KEY: user_input[CONF_API_KEY]},
                    options={CONF_ADDRESSES: [], CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth flow."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            reauth_entry = self._get_reauth_entry()
            session = async_get_clientsession(self.hass)
            client = EtherscanClient(session, user_input[CONF_API_KEY])

            try:
                await client.async_validate_key()
            except EtherscanAuthenticationError:
                errors["base"] = "invalid_auth"
            except EtherscanConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    reauth_entry,
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: EthereumBalanceConfigEntry,
    ) -> EthereumBalanceOptionsFlow:
        """Get the options flow for this handler."""
        return EthereumBalanceOptionsFlow()


class EthereumBalanceOptionsFlow(OptionsFlow):
    """Handle Ethereum Balance options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            raw_text: str = user_input.get(CONF_ADDRESSES, "")
            addresses: list[str] = []
            for line in re.split(r"[,\n]", raw_text):
                addr = line.strip()
                if not addr:
                    continue
                if not ETH_ADDRESS_PATTERN.match(addr):
                    errors[CONF_ADDRESSES] = "invalid_address"
                    break
                addresses.append(addr)

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_ADDRESSES: addresses,
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    },
                )

        current_addresses: list[str] = self.config_entry.options.get(CONF_ADDRESSES, [])
        current_interval: int = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ADDRESSES,
                        default="\n".join(current_addresses),
                    ): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )
