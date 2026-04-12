"""Exceptions for the Ethereum Balance integration."""

from __future__ import annotations

from homeassistant.exceptions import HomeAssistantError


class EthereumBalanceError(HomeAssistantError):
    """Base exception for Ethereum Balance."""


class EtherscanConnectionError(EthereumBalanceError):
    """Raised when unable to connect to Etherscan."""


class EtherscanAuthenticationError(EthereumBalanceError):
    """Raised when the API key is invalid."""


class EtherscanAPIError(EthereumBalanceError):
    """Raised when Etherscan returns an error."""


class EtherscanRateLimitError(EthereumBalanceError):
    """Raised when the API rate limit is exceeded."""
