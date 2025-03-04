"""Support for RuuviTag sensors."""
from __future__ import annotations

from typing import Optional, Union

from sensor_state_data import (
    DeviceKey,
    SensorDescription,
    SensorDeviceClass,
    SensorUpdate,
    Units,
)

from homeassistant import config_entries, const
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorCoordinator,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.sensor import sensor_device_info_to_hass_device_info

from .const import DOMAIN

SENSOR_DESCRIPTIONS = {
    (SensorDeviceClass.TEMPERATURE, Units.TEMP_CELSIUS): SensorEntityDescription(
        key=f"{SensorDeviceClass.TEMPERATURE}_{Units.TEMP_CELSIUS}",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=const.TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (SensorDeviceClass.HUMIDITY, Units.PERCENTAGE): SensorEntityDescription(
        key=f"{SensorDeviceClass.HUMIDITY}_{Units.PERCENTAGE}",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=const.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (SensorDeviceClass.PRESSURE, Units.PRESSURE_HPA): SensorEntityDescription(
        key=f"{SensorDeviceClass.PRESSURE}_{Units.PRESSURE_HPA}",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=const.PRESSURE_HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (
        SensorDeviceClass.VOLTAGE,
        Units.ELECTRIC_POTENTIAL_MILLIVOLT,
    ): SensorEntityDescription(
        key=f"{SensorDeviceClass.VOLTAGE}_{Units.ELECTRIC_POTENTIAL_MILLIVOLT}",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=const.ELECTRIC_POTENTIAL_MILLIVOLT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    (
        SensorDeviceClass.SIGNAL_STRENGTH,
        Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    ): SensorEntityDescription(
        key=f"{SensorDeviceClass.SIGNAL_STRENGTH}_{Units.SIGNAL_STRENGTH_DECIBELS_MILLIWATT}",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=const.SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    (SensorDeviceClass.COUNT, None): SensorEntityDescription(
        key="movement_counter",
        device_class=SensorDeviceClass.COUNT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
}


def _device_key_to_bluetooth_entity_key(
    device_key: DeviceKey,
) -> PassiveBluetoothEntityKey:
    """Convert a device key to an entity key."""
    return PassiveBluetoothEntityKey(device_key.key, device_key.device_id)


def _to_sensor_key(
    description: SensorDescription,
) -> tuple[SensorDeviceClass, Units | None]:
    assert description.device_class is not None
    return (description.device_class, description.native_unit_of_measurement)


def sensor_update_to_bluetooth_data_update(
    sensor_update: SensorUpdate,
) -> PassiveBluetoothDataUpdate:
    """Convert a sensor update to a bluetooth data update."""
    return PassiveBluetoothDataUpdate(
        devices={
            device_id: sensor_device_info_to_hass_device_info(device_info)
            for device_id, device_info in sensor_update.devices.items()
        },
        entity_descriptions={
            _device_key_to_bluetooth_entity_key(device_key): SENSOR_DESCRIPTIONS[
                _to_sensor_key(description)
            ]
            for device_key, description in sensor_update.entity_descriptions.items()
            if _to_sensor_key(description) in SENSOR_DESCRIPTIONS
        },
        entity_data={
            _device_key_to_bluetooth_entity_key(device_key): sensor_values.native_value
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
        entity_names={
            _device_key_to_bluetooth_entity_key(device_key): sensor_values.name
            for device_key, sensor_values in sensor_update.entity_values.items()
        },
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: config_entries.ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ruuvitag BLE sensors."""
    coordinator: PassiveBluetoothProcessorCoordinator = hass.data[DOMAIN][
        entry.entry_id
    ]
    processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    entry.async_on_unload(
        processor.async_add_entities_listener(
            RuuvitagBluetoothSensorEntity, async_add_entities
        )
    )
    entry.async_on_unload(coordinator.async_register_processor(processor))


class RuuvitagBluetoothSensorEntity(
    PassiveBluetoothProcessorEntity[
        PassiveBluetoothDataProcessor[Optional[Union[float, int]]]
    ],
    SensorEntity,
):
    """Representation of a Ruuvitag BLE sensor."""

    @property
    def native_value(self) -> int | float | None:
        """Return the native value."""
        return self.processor.entity_data.get(self.entity_key)
