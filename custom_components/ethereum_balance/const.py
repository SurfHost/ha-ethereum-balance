"""Constants for the Ethereum Balance integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "ethereum_balance"

CONF_API_KEY: Final = "api_key"
CONF_ADDRESSES: Final = "addresses"
CONF_WALLETS: Final = "wallets"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_OER_API_KEY: Final = "oer_api_key"
CONF_LOCAL_CURRENCY: Final = "local_currency"

DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 3600

ETHERSCAN_API_URL: Final = "https://api.etherscan.io/v2/api"
ETHERSCAN_CHAIN_ID: Final = "1"

OER_API_URL: Final = "https://openexchangerates.org/api"
OER_REFRESH_INTERVAL: Final = 7200

WEI_PER_ETH: Final = 10**18
MAX_BATCH_ADDRESSES: Final = 20
