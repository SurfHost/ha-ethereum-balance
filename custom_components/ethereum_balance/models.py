"""Data models for the Ethereum Balance integration."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class WalletBalance:
    """Represents an Ethereum wallet balance."""

    address: str
    balance_wei: int
    balance_eth: float


@dataclass(frozen=True, slots=True)
class EthPrice:
    """Represents the current ETH price."""

    usd: float
    btc: float


@dataclass(slots=True)
class EthereumData:
    """Container for all Ethereum data from the coordinator."""

    wallets: dict[str, WalletBalance] = field(default_factory=dict)
    eth_price: EthPrice | None = None
