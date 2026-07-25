"""Sensor platform for the Ethereum Balance integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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

from .const import CONF_LOCAL_CURRENCY, CONF_OER_API_KEY
from .coordinator import EthereumBalanceConfigEntry, get_wallets
from .entity import EthereumBalanceEntity
from .models import EthereumData


@dataclass(frozen=True, kw_only=True)
class EthereumBalanceSensorDescription(SensorEntityDescription):
    """Describes an Ethereum Balance sensor entity."""

    # Both callables must take exactly one argument. A lambda with extra
    # default-valued parameters (the usual closure-binding trick) no longer
    # matches this annotation, so mypy cannot infer the "data" type and strict
    # mode fails with "Cannot infer type of lambda". The factories below close
    # over their locals directly instead.
    value_fn: Callable[[EthereumData], StateType] = lambda _: None
    extra_attrs_fn: Callable[[EthereumData], dict[str, Any]] | None = None


ETH_PRICE_SENSOR = EthereumBalanceSensorDescription(
    key="eth_price",
    name="ETH price",
    native_unit_of_measurement="USD",
    device_class=SensorDeviceClass.MONETARY,
    state_class=None,
    suggested_display_precision=2,
    icon="mdi:currency-usd",
    value_fn=lambda data: round(data.eth_price.usd, 2) if data.eth_price else None,
)


def _make_balance_sensor(name: str, address: str) -> EthereumBalanceSensorDescription:
    """Create a balance sensor description for a wallet."""
    addr_lower = address.lower()

    return EthereumBalanceSensorDescription(
        key=f"balance_{addr_lower}",
        name=f"{name} balance",
        native_unit_of_measurement="ETH",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=8,
        icon="mdi:ethereum",
        value_fn=lambda data: (
            data.wallets[addr_lower].balance_eth if addr_lower in data.wallets else None
        ),
        extra_attrs_fn=lambda data: (
            {
                "address": data.wallets[addr_lower].address,
                "balance_wei": str(data.wallets[addr_lower].balance_wei),
            }
            if addr_lower in data.wallets
            else {}
        ),
    )


def _make_value_sensor(name: str, address: str) -> EthereumBalanceSensorDescription:
    """Create a USD value sensor description for a wallet."""
    addr_lower = address.lower()

    return EthereumBalanceSensorDescription(
        key=f"value_{addr_lower}",
        name=f"{name} value",
        native_unit_of_measurement="USD",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:currency-usd",
        value_fn=lambda data: (
            round(data.wallets[addr_lower].balance_eth * data.eth_price.usd, 2)
            if addr_lower in data.wallets and data.eth_price
            else None
        ),
        extra_attrs_fn=lambda data: (
            {
                "address": data.wallets[addr_lower].address,
                "eth_balance": data.wallets[addr_lower].balance_eth,
                "eth_price_usd": data.eth_price.usd if data.eth_price else None,
            }
            if addr_lower in data.wallets
            else {}
        ),
    )


def _make_local_value_sensor(
    name: str, address: str, currency: str
) -> EthereumBalanceSensorDescription:
    """Create a local currency value sensor description for a wallet."""
    addr_lower = address.lower()

    return EthereumBalanceSensorDescription(
        key=f"local_value_{addr_lower}",
        name=f"{name} value {currency}",
        native_unit_of_measurement=currency,
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=2,
        icon="mdi:cash-multiple",
        value_fn=lambda data: (
            round(
                data.wallets[addr_lower].balance_eth * data.eth_price.usd * data.exchange_rate.rate,
                2,
            )
            if addr_lower in data.wallets and data.eth_price and data.exchange_rate
            else None
        ),
        extra_attrs_fn=lambda data: (
            {
                "address": data.wallets[addr_lower].address,
                "eth_balance": data.wallets[addr_lower].balance_eth,
                "eth_price_usd": data.eth_price.usd if data.eth_price else None,
                "exchange_rate": data.exchange_rate.rate if data.exchange_rate else None,
            }
            if addr_lower in data.wallets
            else {}
        ),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EthereumBalanceConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ethereum Balance sensors."""
    coordinator = entry.runtime_data
    oer_key: str = entry.options.get(CONF_OER_API_KEY, "")
    local_currency: str = entry.options.get(CONF_LOCAL_CURRENCY, "")
    has_local_currency = bool(oer_key and local_currency)

    entities: list[EthereumBalanceSensor] = [
        EthereumBalanceSensor(coordinator, ETH_PRICE_SENSOR),
    ]

    if has_local_currency:
        eth_price_local = EthereumBalanceSensorDescription(
            key=f"eth_price_{local_currency.lower()}",
            name=f"ETH price {local_currency}",
            native_unit_of_measurement=local_currency,
            device_class=SensorDeviceClass.MONETARY,
            state_class=None,
            suggested_display_precision=2,
            icon="mdi:cash-multiple",
            value_fn=lambda data: (
                round(data.eth_price.usd * data.exchange_rate.rate, 2)
                if data.eth_price and data.exchange_rate
                else None
            ),
            extra_attrs_fn=lambda data: (
                {
                    "usd_price": data.eth_price.usd,
                    "exchange_rate": data.exchange_rate.rate,
                }
                if data.eth_price and data.exchange_rate
                else {}
            ),
        )
        entities.append(EthereumBalanceSensor(coordinator, eth_price_local))

    for wallet in get_wallets(entry):
        name = wallet["name"] or "Wallet"
        address = wallet["address"]
        entities.append(
            EthereumBalanceSensor(coordinator, _make_balance_sensor(name, address)),
        )
        entities.append(
            EthereumBalanceSensor(coordinator, _make_value_sensor(name, address)),
        )
        if has_local_currency:
            entities.append(
                EthereumBalanceSensor(
                    coordinator, _make_local_value_sensor(name, address, local_currency)
                ),
            )

    async_add_entities(entities)


class EthereumBalanceSensor(EthereumBalanceEntity, SensorEntity):
    """Ethereum Balance sensor entity."""

    entity_description: EthereumBalanceSensorDescription

    @property
    def native_value(self) -> StateType:
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
