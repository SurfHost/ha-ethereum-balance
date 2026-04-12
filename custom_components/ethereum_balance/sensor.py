"""Sensor platform for the Ethereum Balance integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import CONF_ADDRESSES, CONF_WALLETS
from .coordinator import EthereumBalanceConfigEntry, EthereumBalanceCoordinator
from .entity import EthereumBalanceEntity
from .models import EthereumData


@dataclass(frozen=True, kw_only=True)
class EthereumBalanceSensorDescription(SensorEntityDescription):
    """Describes an Ethereum Balance sensor entity."""

    value_fn: Callable[[EthereumData], StateType | datetime] = lambda _: None
    extra_attrs_fn: Callable[[EthereumData], dict[str, Any]] | None = None


ETH_PRICE_SENSOR = EthereumBalanceSensorDescription(
    key="eth_price",
    translation_key="eth_price",
    name="ETH price",
    native_unit_of_measurement="USD",
    device_class=SensorDeviceClass.MONETARY,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
    icon="mdi:currency-usd",
    value_fn=lambda data: round(data.eth_price.usd, 2) if data.eth_price else None,
    extra_attrs_fn=lambda data: {"btc_price": data.eth_price.btc} if data.eth_price else {},
)


def _make_balance_sensor(
    name: str, address: str
) -> EthereumBalanceSensorDescription:
    """Create a balance sensor description for a wallet."""
    addr_lower = address.lower()

    return EthereumBalanceSensorDescription(
        key=f"balance_{addr_lower}",
        translation_key="wallet_balance",
        name=f"{name} balance",
        native_unit_of_measurement="ETH",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=8,
        icon="mdi:ethereum",
        value_fn=lambda data, a=addr_lower: data.wallets[a].balance_eth
        if a in data.wallets
        else None,
        extra_attrs_fn=lambda data, a=addr_lower: {
            "address": data.wallets[a].address,
            "balance_wei": str(data.wallets[a].balance_wei),
        }
        if a in data.wallets
        else {},
    )


def _make_value_sensor(
    name: str, address: str
) -> EthereumBalanceSensorDescription:
    """Create a USD value sensor description for a wallet."""
    addr_lower = address.lower()

    return EthereumBalanceSensorDescription(
        key=f"value_{addr_lower}",
        translation_key="wallet_value",
        name=f"{name} value",
        native_unit_of_measurement="USD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:currency-usd",
        value_fn=lambda data, a=addr_lower: round(
            data.wallets[a].balance_eth * data.eth_price.usd, 2
        )
        if a in data.wallets and data.eth_price
        else None,
        extra_attrs_fn=lambda data, a=addr_lower: {
            "address": data.wallets[a].address,
            "eth_balance": data.wallets[a].balance_eth,
            "eth_price": data.eth_price.usd if data.eth_price else None,
        }
        if a in data.wallets
        else {},
    )


def _get_wallets(entry: EthereumBalanceConfigEntry) -> list[dict[str, str]]:
    """Get wallet list from options, supporting both old and new format."""
    wallets: list[dict[str, str]] = entry.options.get(CONF_WALLETS, [])
    if wallets:
        return wallets
    # Fallback to old format (plain address list)
    addresses: list[str] = entry.options.get(CONF_ADDRESSES, [])
    return [
        {"name": f"{a[:6]}...{a[-4:]}", "address": a}
        for a in addresses
    ]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EthereumBalanceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ethereum Balance sensors."""
    coordinator = entry.runtime_data

    entities: list[EthereumBalanceSensor] = [
        EthereumBalanceSensor(coordinator, ETH_PRICE_SENSOR),
    ]

    for wallet in _get_wallets(entry):
        name = wallet["name"]
        address = wallet["address"]
        entities.append(
            EthereumBalanceSensor(coordinator, _make_balance_sensor(name, address)),
        )
        entities.append(
            EthereumBalanceSensor(coordinator, _make_value_sensor(name, address)),
        )

    async_add_entities(entities)


class EthereumBalanceSensor(EthereumBalanceEntity, SensorEntity):
    """Ethereum Balance sensor entity."""

    entity_description: EthereumBalanceSensorDescription

    @property
    def native_value(self) -> StateType | datetime:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None or self.entity_description.extra_attrs_fn is None:
            return None
        return self.entity_description.extra_attrs_fn(self.coordinator.data)
