"""DataUpdateCoordinator for the Ethereum Balance integration."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EtherscanClient
from .const import CONF_ADDRESSES, CONF_WALLETS, DEFAULT_SCAN_INTERVAL, DOMAIN
from .errors import (
    EtherscanAuthenticationError,
    EtherscanConnectionError,
    EtherscanRateLimitError,
)
from .models import EthereumData

_LOGGER = logging.getLogger(__name__)

type EthereumBalanceConfigEntry = ConfigEntry[EthereumBalanceCoordinator]


def get_wallet_addresses(entry: ConfigEntry[EthereumBalanceCoordinator]) -> list[str]:
    """Extract addresses from config entry options, supporting both old and new format."""
    wallets: list[dict[str, str]] = entry.options.get(CONF_WALLETS, [])
    if wallets:
        return [w["address"] for w in wallets]
    # Fallback to old format
    return entry.options.get(CONF_ADDRESSES, [])


class EthereumBalanceCoordinator(DataUpdateCoordinator[EthereumData]):
    """Coordinator to manage fetching Ethereum data."""

    config_entry: EthereumBalanceConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: EtherscanClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client

    async def _async_update_data(self) -> EthereumData:
        """Fetch data from Etherscan."""
        data = self.data or EthereumData()

        try:
            addresses = get_wallet_addresses(self.config_entry)
            if addresses:
                data.wallets = await self.client.async_get_balances(addresses)
            data.eth_price = await self.client.async_get_eth_price()
        except EtherscanAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (EtherscanConnectionError, EtherscanRateLimitError) as err:
            raise UpdateFailed(str(err)) from err

        return data
