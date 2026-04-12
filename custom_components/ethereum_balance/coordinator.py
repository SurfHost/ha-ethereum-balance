"""DataUpdateCoordinator for the Ethereum Balance integration."""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EtherscanClient, OpenExchangeRatesClient
from .const import CONF_WALLETS, DEFAULT_SCAN_INTERVAL, DOMAIN, OER_REFRESH_INTERVAL
from .errors import (
    EtherscanAPIError,
    EtherscanAuthenticationError,
    EtherscanConnectionError,
    EtherscanRateLimitError,
    OERAuthenticationError,
    OERConnectionError,
)
from .models import EthereumData

_LOGGER = logging.getLogger(__name__)

type EthereumBalanceConfigEntry = ConfigEntry[EthereumBalanceCoordinator]


def get_wallets(entry: ConfigEntry[EthereumBalanceCoordinator]) -> list[dict[str, str]]:
    """Get wallet list from config entry options."""
    return entry.options.get(CONF_WALLETS, [])


def get_wallet_addresses(entry: ConfigEntry[EthereumBalanceCoordinator]) -> list[str]:
    """Extract addresses from config entry options."""
    return [w["address"] for w in get_wallets(entry)]


class EthereumBalanceCoordinator(DataUpdateCoordinator[EthereumData]):
    """Coordinator to manage fetching Ethereum data."""

    config_entry: EthereumBalanceConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: EtherscanClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
        oer_client: OpenExchangeRatesClient | None = None,
        local_currency: str | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.oer_client = oer_client
        self.local_currency = local_currency
        self._last_oer_fetch: float = 0

    async def _async_update_data(self) -> EthereumData:
        """Fetch data from Etherscan and optionally Open Exchange Rates."""
        data = self.data or EthereumData()

        try:
            addresses = get_wallet_addresses(self.config_entry)
            if addresses:
                data.wallets = await self.client.async_get_balances(addresses)
            else:
                data.wallets = {}
            data.eth_price = await self.client.async_get_eth_price()
        except EtherscanAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except (EtherscanConnectionError, EtherscanRateLimitError, EtherscanAPIError) as err:
            raise UpdateFailed(str(err)) from err

        # Fetch exchange rate if OER is configured, with 2-hour caching
        if self.oer_client and self.local_currency:
            now = time.monotonic()
            if now - self._last_oer_fetch > OER_REFRESH_INTERVAL or data.exchange_rate is None:
                try:
                    data.exchange_rate = await self.oer_client.async_get_rate(
                        self.local_currency
                    )
                    self._last_oer_fetch = now
                    _LOGGER.debug(
                        "Fetched exchange rate: 1 USD = %s %s",
                        data.exchange_rate.rate,
                        data.exchange_rate.currency,
                    )
                except OERAuthenticationError:
                    _LOGGER.warning("OER API key is invalid, skipping exchange rate update")
                except OERConnectionError as err:
                    _LOGGER.warning("Failed to fetch exchange rate: %s", err)

        return data
