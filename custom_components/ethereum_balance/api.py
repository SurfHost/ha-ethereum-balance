"""Etherscan API client for the Ethereum Balance integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import aiohttp

from .const import ETHERSCAN_API_URL, MAX_BATCH_ADDRESSES, WEI_PER_ETH
from .errors import (
    EtherscanAPIError,
    EtherscanAuthenticationError,
    EtherscanConnectionError,
    EtherscanRateLimitError,
)
from .models import EthPrice, WalletBalance

_LOGGER = logging.getLogger(__name__)


class EtherscanClient:
    """Client for the Etherscan API with built-in rate limiting."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key
        self._semaphore = asyncio.Semaphore(3)
        self._call_timestamps: list[float] = []

    async def _throttled_get(self, params: dict[str, str]) -> Any:
        """Make a rate-limited GET request to Etherscan."""
        async with self._semaphore:
            now = time.monotonic()
            # Remove timestamps older than 1 second
            self._call_timestamps = [t for t in self._call_timestamps if now - t < 1.0]
            # If we've made 3 calls in the last second, wait
            if len(self._call_timestamps) >= 3:
                sleep_time = 1.0 - (now - self._call_timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    self._call_timestamps = self._call_timestamps[1:]

            self._call_timestamps.append(time.monotonic())
            params["apikey"] = self._api_key

            try:
                async with self._session.get(
                    ETHERSCAN_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
            except (aiohttp.ClientError, TimeoutError) as err:
                raise EtherscanConnectionError(
                    f"Cannot connect to Etherscan: {err}"
                ) from err

            if data.get("status") == "0":
                result = str(data.get("result", ""))
                message = str(data.get("message", ""))
                if "invalid api" in result.lower() or "invalid api" in message.lower():
                    raise EtherscanAuthenticationError("Invalid Etherscan API key")
                if "rate limit" in result.lower() or "rate limit" in message.lower():
                    raise EtherscanRateLimitError("Etherscan API rate limit exceeded")
                # "No transactions found" is not an error for balance queries
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

            if isinstance(result, list):
                for entry in result:
                    addr = str(entry["account"]).lower()
                    balance_wei = int(entry["balance"])
                    balance_eth = round(balance_wei / WEI_PER_ETH, 8)
                    wallets[addr] = WalletBalance(
                        address=entry["account"],
                        balance_wei=balance_wei,
                        balance_eth=balance_eth,
                    )

        return wallets

    async def async_get_eth_price(self) -> EthPrice:
        """Fetch the current ETH price in USD and BTC."""
        result = await self._throttled_get(
            {
                "module": "stats",
                "action": "ethprice",
            }
        )

        return EthPrice(
            usd=float(result["ethusd"]),
            btc=float(result["ethbtc"]),
        )
