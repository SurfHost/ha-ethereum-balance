# Changelog

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
