# Changelog

## [0.3.4] - 2026-07-25

### Fixed
- **`requires-python` was unsatisfiable.** It declared `>=3.13` alongside `homeassistant>=2026.4.0`, but Home Assistant 2026.3 and later require Python 3.14.2. The resolver therefore silently fell back to Home Assistant 2025.4.4, so type checking ran against stubs a year older than the declared floor. The floor is now 3.14.2.
- `pyproject.toml` was left at `0.3.2` when `manifest.json` moved to `0.3.3`. The two are synced, and the release gate now compares the tag against both.

### Added
- MIT `LICENSE`, which the repository had never shipped.
- CI now runs `ruff check`, `ruff format --check` and strict `mypy`. Previously the workflow validated HACS and hassfest metadata only, so no line of Python was ever executed by CI.
- A release gate that fails a tag push when the tag disagrees with the version in `manifest.json` or `pyproject.toml`.

### Changed
- `.claude/` is gitignored, which was letting three stale worktree copies of the integration be linted.

## [0.3.3] - 2026-04-18

### Fixed
- ETH price sensors no longer produce a HA warning about incompatible `state_class`; price sensors now have no state class (spot price, not cumulative)

## [0.3.2] - 2026-04-12

### Fixed
- Wallets without a name now show as "Wallet balance" and "Wallet value" instead of the truncated address
- Options flow now shows plain address (not Name:Address) when no name was given
- Re-editing wallets no longer corrupts the address format

## [0.3.1] - 2026-04-12

### Fixed
- Rate limiter now uses asyncio.Lock for proper atomic sliding-window enforcement
- Coordinator clears wallet data when all wallets are removed
- EtherscanAPIError and OERAuthenticationError properly caught in coordinator
- Defensive parsing for malformed Etherscan API responses

### Changed
- Removed legacy address format support (CONF_ADDRESSES)
- Consolidated wallet helpers between coordinator and sensor
- Cleaned up unused translation keys and imports

## [0.3.0] - 2026-04-12

### Added
- Open Exchange Rates integration for local currency conversion (EUR, GBP, etc.)
- Local currency value sensor per wallet (e.g. "Savings value EUR")
- OER API key and local currency fields in options flow
- Validation for OER API key on save

### Changed
- Default update interval changed from 300s to 30s
- Minimum update interval changed from 60s to 10s
- Exchange rates cached for 2 hours to stay within OER free tier (1,000 requests/month)

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
