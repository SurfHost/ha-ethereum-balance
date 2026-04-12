# Ethereum Balance for Home Assistant

[![Validate](https://github.com/SurfHost/ha-ethereum-balance/actions/workflows/validate.yml/badge.svg)](https://github.com/SurfHost/ha-ethereum-balance/actions/workflows/validate.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

[![Add Repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SurfHost&repository=ha-ethereum-balance&category=integration)
[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ethereum_balance)

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

1. Go to **Settings** > **Devices & Services** > **Add Integration**
2. Search for "Ethereum Balance"
3. Enter your Etherscan API key
4. After setup, click **Configure** to add wallet addresses

### Options

| Option | Default | Description |
|--------|---------|-------------|
| Wallet addresses | _(empty)_ | One Ethereum address per line (0x + 40 hex chars) |
| Update interval | 300 | Polling interval in seconds (60-3600) |

## Sensors

### ETH Price
- **State**: Current ETH price in USD
- **Attributes**: `btc_price`

### Wallet Balance (per address)
- **State**: ETH balance (8 decimal precision)
- **Attributes**: `address`, `balance_wei`, `usd_value`

## Rate Limits

The integration is designed to stay well within [Etherscan's free tier limits](https://docs.etherscan.io/resources/rate-limits) (3 calls/sec, 100k calls/day):

- Batch queries fetch up to 20 wallet balances in a single API call
- Default 5-minute interval = ~576 calls/day (0.6% of daily limit)
- Built-in sliding-window rate limiter prevents exceeding 3 calls/sec

## Roadmap

- [ ] Open Exchange Rates integration for USD to EUR/other currency conversion

## License

MIT
