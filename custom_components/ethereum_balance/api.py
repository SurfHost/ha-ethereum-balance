"""API clients for the Ethereum Balance integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from .const import (
    ETHERSCAN_API_URL,
    ETHERSCAN_CHAIN_ID,
    MAX_BATCH_ADDRESSES,
    OER_API_URL,
    WEI_PER_ETH,
)
from .errors import (
    EtherscanAPIError,
    EtherscanAuthenticationError,
    EtherscanConnectionError,
    EtherscanRateLimitError,
    OERAuthenticationError,
    OERConnectionError,
)
from .models import EthPrice, ExchangeRate, WalletBalance

_LOGGER = logging.getLogger(__name__)


class EtherscanClient:
    """Client for the Etherscan API with built-in rate limiting."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key
        self._lock = asyncio.Lock()
        self._call_timestamps: list[float] = []

    async def _throttled_get(self, params: dict[str, str]) -> Any:
        """Make a rate-limited GET request to Etherscan."""
        async with self._lock:
            now = time.monotonic()
            # Remove timestamps older than 1 second
            self._call_timestamps = [t for t in self._call_timestamps if now - t < 1.0]
            # If we've made 3 calls in the last second, wait
            if len(self._call_timestamps) >= 3:
                sleep_time = 1.0 - (now - self._call_timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

            self._call_timestamps.append(time.monotonic())

        params["apikey"] = self._api_key
        params["chainid"] = ETHERSCAN_CHAIN_ID

        try:
            async with self._session.get(
                ETHERSCAN_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                data = await response.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise EtherscanConnectionError(f"Cannot connect to Etherscan: {err}") from err

        if data.get("status") == "0":
            result = str(data.get("result", ""))
            message = str(data.get("message", ""))
            if "invalid api" in result.lower() or "invalid api" in message.lower():
                raise EtherscanAuthenticationError("Invalid Etherscan API key")
            if "rate limit" in result.lower() or "rate limit" in message.lower():
                raise EtherscanRateLimitError("Etherscan API rate limit exceeded")
            if "no transactions found" not in result.lower():
                raise EtherscanAPIError(f"Etherscan API error: {result}")

        return data.get("result")

    async def async_validate_key(self) -> bool:
        """Validate the API key by fetching ETH price."""
        await self.async_get_eth_price()
        return True

    async def async_get_balances(self, addresses: list[str]) -> dict[str, WalletBalance]:
        """Fetch balances for multiple addresses, batching as needed."""
        wallets: dict[str, WalletBalance] = {}

        for i in range(0, len(addresses), MAX_BATCH_ADDRESSES):
            chunk = addresses[i : i + MAX_BATCH_ADDRESSES]
            result = await self._throttled_get(
                {
                    "module": "account",
                    "action": "balancemulti",
                    "address": ",".join(chunk),
                    "tag": "latest",
                }
            )

            if not isinstance(result, list):
                _LOGGER.warning("Unexpected balance response format: %s", type(result))
                continue

            for entry in result:
                try:
                    addr = str(entry["account"]).lower()
                    balance_wei = int(entry["balance"])
                    balance_eth = round(balance_wei / WEI_PER_ETH, 8)
                    wallets[addr] = WalletBalance(
                        address=entry["account"],
                        balance_wei=balance_wei,
                        balance_eth=balance_eth,
                    )
                except (KeyError, ValueError) as err:
                    _LOGGER.warning("Failed to parse balance entry: %s", err)

        return wallets

    async def async_get_eth_price(self) -> EthPrice:
        """Fetch the current ETH price in USD and BTC."""
        result = await self._throttled_get(
            {
                "module": "stats",
                "action": "ethprice",
            }
        )

        try:
            return EthPrice(
                usd=float(result["ethusd"]),
                btc=float(result["ethbtc"]),
            )
        except (KeyError, TypeError, ValueError) as err:
            raise EtherscanAPIError(f"Unexpected ethprice response: {err}") from err


class OpenExchangeRatesClient:
    """Client for the Open Exchange Rates API."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key

    async def async_validate_key(self) -> bool:
        """Validate the API key by fetching latest rates."""
        try:
            async with self._session.get(
                f"{OER_API_URL}/latest.json",
                params={"app_id": self._api_key},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (401, 403):
                    raise OERAuthenticationError("Invalid Open Exchange Rates API key")
                response.raise_for_status()
                return True
        except OERAuthenticationError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise OERConnectionError(f"Cannot connect to Open Exchange Rates: {err}") from err

    async def async_get_rate(self, currency: str) -> ExchangeRate:
        """Fetch the exchange rate from USD to the given currency."""
        try:
            async with self._session.get(
                f"{OER_API_URL}/latest.json",
                params={
                    "app_id": self._api_key,
                    "symbols": currency.upper(),
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status in (401, 403):
                    raise OERAuthenticationError("Invalid Open Exchange Rates API key")
                response.raise_for_status()
                data = await response.json()
        except OERAuthenticationError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise OERConnectionError(f"Cannot connect to Open Exchange Rates: {err}") from err

        rates: dict[str, float] = data.get("rates", {})
        currency_upper = currency.upper()
        if currency_upper not in rates:
            raise OERConnectionError(f"Currency {currency_upper} not found in OER response")

        return ExchangeRate(
            currency=currency_upper,
            rate=float(rates[currency_upper]),
        )
