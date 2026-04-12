# Ethereum Balance for Home Assistant

[![Validate](https://github.com/SurfHost/ha-ethereum-balance/actions/workflows/validate.yml/badge.svg)](https://github.com/SurfHost/ha-ethereum-balance/actions/workflows/validate.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration to monitor Ethereum wallet balances using the [Etherscan API](https://etherscan.io/apis).

## Features

- Track ETH balance for one or more Ethereum wallets
- Real-time ETH/USD price sensor
- USD value calculation per wallet
- Built-in rate limiting to stay within Etherscan free tier limits
- Batch API queries for efficient multi-wallet monitoring
- Configurable update interval (default: 5 minutes)

## Requirements

- Home Assistant 2026.4 or newer
- Free Etherscan API key ([get one here](https://etherscan.io/apis))

## Installation

### HACS (Recommended)

[![Add Repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SurfHost&repository=ha-ethereum-balance&category=integration)

Or manually:

1. Open HACS in Home Assistant
2. Click the three dots menu and select **Custom repositories**
3. Add `https://github.com/SurfHost/ha-ethereum-balance` with category **Integration**
4. Search for "Ethereum Balance" and install it
5. Restart Home Assistant

### Manual

1. Download the `custom_components/ethereum_balance` folder
2. Place it in your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ethereum_balance)

Or manually:

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "Ethereum Balance"
3. Enter your Etherscan API key
4. After setup, click **Configure** to add wallet addresses

### Options

| Option | Default | Description |
|--------|---------|-------------|
| Wallets | _(empty)_ | One wallet per line as `Name:0xAddress` (name is optional) |
| Update interval | 30 | Polling interval in seconds (10-3600) |
| OER API key | _(empty)_ | Open Exchange Rates API key (optional, for local currency) |
| Local currency | _(empty)_ | Target currency code, e.g. `EUR`, `GBP` (requires OER key) |

**Example wallet input:**
```
My Savings:0x1234567890abcdef1234567890abcdef12345678
Cold Wallet:0xabcdef1234567890abcdef1234567890abcdef12
0x9876543210fedcba9876543210fedcba98765432
```

## Local Currency Conversion

To show wallet values in your local currency (e.g. EUR):

1. Get a free API key at [openexchangerates.org](https://openexchangerates.org/signup/free)
2. In the integration options, enter the OER API key and your currency code (e.g. `EUR`)
3. A new sensor per wallet appears showing the value in your local currency

Exchange rates are cached and refreshed every 2 hours to stay within the OER free tier (1,000 requests/month).

## Sensors

### ETH Price
- **State**: Current ETH price in USD
- **Attributes**: `btc_price`

### Wallet Balance (per wallet)
- **State**: ETH balance (8 decimal precision)
- **Name**: Uses your custom name (e.g. "My Savings balance")
- **Attributes**: `address`, `balance_wei`

### Wallet Value (per wallet)
- **State**: USD value of the wallet
- **Name**: Uses your custom name (e.g. "My Savings value")
- **Attributes**: `address`, `eth_balance`, `eth_price_usd`

### Wallet Local Value (per wallet, optional)
- **State**: Value in your local currency (e.g. EUR)
- **Name**: Uses your custom name (e.g. "My Savings value EUR")
- **Attributes**: `address`, `eth_balance`, `eth_price_usd`, `exchange_rate`
- Only created when OER API key and local currency are configured

## Rate Limits

### Etherscan (3 calls/sec, 100k calls/day)
- Batch queries fetch up to 20 wallet balances in a single API call
- Built-in sliding-window rate limiter prevents exceeding 3 calls/sec

### Open Exchange Rates (1,000 requests/month)
- Exchange rates cached for 2 hours (~360 calls/month)

## License

MIT
