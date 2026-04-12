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

from .api import EtherscanClient, OpenExchangeRatesClient
from .const import (
    CONF_API_KEY,
    CONF_LOCAL_CURRENCY,
    CONF_OER_API_KEY,
    CONF_SCAN_INTERVAL,
    CONF_WALLETS,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import EthereumBalanceConfigEntry
from .errors import EtherscanAuthenticationError, EtherscanConnectionError, OERAuthenticationError, OERConnectionError

_LOGGER = logging.getLogger(__name__)

ETH_ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


def _parse_wallets(raw_text: str) -> tuple[list[dict[str, str]], str | None]:
    """Parse wallet entries from text input.

    Accepts lines in format:
        Name:0xAddress
        0xAddress  (name defaults to shortened address)

    Returns (wallets, error_key) where error_key is None on success.
    """
    wallets: list[dict[str, str]] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if ":" in line:
            name, _, address = line.partition(":")
            name = name.strip()
            address = address.strip()
        else:
            address = line
            name = f"{address[:6]}...{address[-4:]}"

        if not ETH_ADDRESS_PATTERN.match(address):
            return [], "invalid_address"

        if not name:
            name = f"{address[:6]}...{address[-4:]}"

        wallets.append({"name": name, "address": address})

    return wallets, None


def _wallets_to_text(wallets: list[dict[str, str]]) -> str:
    """Convert wallet list back to text for the form."""
    lines: list[str] = []
    for wallet in wallets:
        lines.append(f"{wallet['name']}:{wallet['address']}")
    return "\n".join(lines)


class EthereumBalanceConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ethereum Balance."""

    VERSION = 3

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
                    options={
                        CONF_WALLETS: [],
                        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                        CONF_OER_API_KEY: "",
                        CONF_LOCAL_CURRENCY: "",
                    },
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
            # Parse wallets
            raw_text: str = user_input.get(CONF_WALLETS, "")
            wallets, error = _parse_wallets(raw_text)
            if error:
                errors[CONF_WALLETS] = error

            # Validate OER key if provided
            oer_key: str = user_input.get(CONF_OER_API_KEY, "").strip()
            local_currency: str = user_input.get(CONF_LOCAL_CURRENCY, "").strip().upper()

            if oer_key and local_currency:
                session = async_get_clientsession(self.hass)
                oer_client = OpenExchangeRatesClient(session, oer_key)
                try:
                    await oer_client.async_validate_key()
                except OERAuthenticationError:
                    errors[CONF_OER_API_KEY] = "invalid_oer_key"
                except OERConnectionError:
                    errors[CONF_OER_API_KEY] = "cannot_connect_oer"
            elif oer_key and not local_currency:
                errors[CONF_LOCAL_CURRENCY] = "currency_required"
            elif local_currency and not oer_key:
                errors[CONF_OER_API_KEY] = "oer_key_required"

            if not errors:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_WALLETS: wallets,
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                        CONF_OER_API_KEY: oer_key,
                        CONF_LOCAL_CURRENCY: local_currency,
                    },
                )

        current_wallets: list[dict[str, str]] = self.config_entry.options.get(
            CONF_WALLETS, []
        )
        current_interval: int = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        current_oer_key: str = self.config_entry.options.get(CONF_OER_API_KEY, "")
        current_currency: str = self.config_entry.options.get(CONF_LOCAL_CURRENCY, "")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_WALLETS,
                        default=_wallets_to_text(current_wallets),
                    ): str,
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                    vol.Optional(
                        CONF_OER_API_KEY,
                        default=current_oer_key,
                    ): str,
                    vol.Optional(
                        CONF_LOCAL_CURRENCY,
                        default=current_currency,
                    ): str,
                }
            ),
            errors=errors,
        )
