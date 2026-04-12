# Changelog

## [0.2.0] - 2026-04-12

### Added
- Custom wallet names (format: `Name:0xAddress` in options)
- USD value sensor per wallet (separate from balance sensor)

### Changed
- Migrated to Etherscan API V2
- Wallet config changed from plain addresses to named entries
- Backwards compatible with v0.1.0 address-only format

## [0.1.0] - 2026-04-12

### Added
- Initial release
- Etherscan API integration with API key authentication
- ETH balance tracking for multiple wallet addresses
- ETH/USD price sensor with BTC price attribute
- USD value calculation per wallet
- Configurable update interval (60-3600 seconds, default 300)
- Built-in rate limiting (3 calls/sec sliding window)
- Batch balance queries (up to 20 addresses per API call)
- Config flow with API key validation
- Options flow for managing wallet addresses
- Reauth flow for expired/invalid API keys
- HACS compatible
