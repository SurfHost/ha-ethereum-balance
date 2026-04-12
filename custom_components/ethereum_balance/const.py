"""Constants for the Ethereum Balance integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ethereum_balance"

CONF_API_KEY: Final = "api_key"
CONF_ADDRESSES: Final = "addresses"
CONF_SCAN_INTERVAL: Final = "scan_interval"

DEFAULT_SCAN_INTERVAL: Final = 300
MIN_SCAN_INTERVAL: Final = 60
MAX_SCAN_INTERVAL: Final = 3600

ETHERSCAN_API_URL: Final = "https://api.etherscan.io/api"

WEI_PER_ETH: Final = 10**18
MAX_BATCH_ADDRESSES: Final = 20
