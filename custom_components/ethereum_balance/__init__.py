"""Ethereum Balance integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EtherscanClient, OpenExchangeRatesClient
from .const import (
    CONF_API_KEY,
    CONF_LOCAL_CURRENCY,
    CONF_OER_API_KEY,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import EthereumBalanceConfigEntry, EthereumBalanceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: EthereumBalanceConfigEntry) -> bool:
    """Set up Ethereum Balance from a config entry."""
    session = async_get_clientsession(hass)
    client = EtherscanClient(session, entry.data[CONF_API_KEY])

    # Set up OER client if configured
    oer_client: OpenExchangeRatesClient | None = None
    local_currency: str | None = None
    oer_key: str = entry.options.get(CONF_OER_API_KEY, "")
    currency: str = entry.options.get(CONF_LOCAL_CURRENCY, "")
    if oer_key and currency:
        oer_client = OpenExchangeRatesClient(session, oer_key)
        local_currency = currency.upper()

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = EthereumBalanceCoordinator(
        hass, client, scan_interval, oer_client, local_currency
    )

    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: EthereumBalanceConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: EthereumBalanceConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
