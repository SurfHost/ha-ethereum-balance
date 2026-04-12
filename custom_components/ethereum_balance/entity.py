"""Base entity for the Ethereum Balance integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EthereumBalanceCoordinator


class EthereumBalanceEntity(CoordinatorEntity[EthereumBalanceCoordinator]):
    """Base entity for Ethereum Balance sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EthereumBalanceCoordinator,
        description: EntityDescription,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Ethereum",
            manufacturer="Etherscan",
            model="Ethereum Blockchain",
            entry_type=DeviceEntryType.SERVICE,
        )
