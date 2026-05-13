"""
Medtrum CGM Sensor Platform for Home Assistant
FIXED: Added Last Bolus sensor
"""

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "medtrum"


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up sensors from config entry"""
    # Get coordinator from hass.data
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        MedtrumGlucoseSensor(coordinator),
        MedtrumSensorBatterySensor(coordinator),
        MedtrumInsulinRemainingsSensor(coordinator),
        MedtrumConnectionSensor(coordinator),
        MedtrumTimestampSensor(coordinator),
        MedtrumGlucoseRateSensor(coordinator),
        MedtrumIOBSensor(coordinator),
        MedtrumLastBolusSensor(coordinator),
    ]

    async_add_entities(sensors, True)


class MedtrumBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for Medtrum sensors"""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_has_entity_name = True

    @property
    def available(self) -> bool:
        """Return if entity is available"""
        return (
            self.coordinator.last_update_success
            and self.get_value() is not None
        )

    def get_value(self):
        """Get value from coordinator data - override in subclass"""
        return None


class MedtrumGlucoseSensor(MedtrumBaseSensor):
    """Glucose sensor"""

    _attr_unique_id = "medtrum_glucose"
    _attr_name = "Glucose"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mmol/L"
    _attr_icon = "mdi:blood-bag"

    def get_value(self):
        return self.coordinator.data.get("glucose")

    @property
    def native_value(self):
        val = self.get_value()
        # Round to 1 decimal place
        return round(val, 1) if val is not None else None


class MedtrumSensorBatterySensor(MedtrumBaseSensor):
    """Sensor battery sensor"""

    _attr_unique_id = "medtrum_sensor_battery"
    _attr_name = "Sensor Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:battery"

    def get_value(self):
        return self.coordinator.data.get("sensor_battery")

    @property
    def native_value(self):
        val = self.get_value()
        return round(val, 0) if val is not None else None


class MedtrumInsulinRemainingsSensor(MedtrumBaseSensor):
    """Insulin remaining in reservoir sensor"""

    _attr_unique_id = "medtrum_insulin_remaining"
    _attr_name = "Insulin Remaining"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "U"
    _attr_icon = "mdi:syringe"

    def get_value(self):
        remaining = self.coordinator.data.get("pump_battery")
        # This is insulin units, not battery percentage
        if remaining is not None:
            return remaining
        return None

    @property
    def native_value(self):
        val = self.get_value()
        return round(val, 1) if val is not None else None


class MedtrumConnectionSensor(MedtrumBaseSensor):
    """Connection status sensor"""

    _attr_unique_id = "medtrum_connected"
    _attr_name = "Connection Status"
    _attr_icon = "mdi:connection"

    def get_value(self):
        return self.coordinator.data.get("connected")

    @property
    def native_value(self):
        val = self.get_value()
        return "Connected" if val else "Disconnected"


class MedtrumTimestampSensor(MedtrumBaseSensor):
    """Data timestamp sensor"""

    _attr_unique_id = "medtrum_timestamp"
    _attr_name = "Last Update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock"

    def get_value(self):
        # Return datetime object, not string
        from datetime import datetime
        ts = self.coordinator.data.get("timestamp")
        if isinstance(ts, datetime):
            return ts
        return None

    @property
    def native_value(self):
        return self.get_value()


class MedtrumGlucoseRateSensor(MedtrumBaseSensor):
    """Glucose rate of change sensor"""

    _attr_unique_id = "medtrum_glucose_rate"
    _attr_name = "Glucose Rate"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "mmol/L/min"
    _attr_icon = "mdi:trending-up"

    def get_value(self):
        return self.coordinator.data.get("glucose_rate")

    @property
    def native_value(self):
        val = self.get_value()
        # Round to 2 decimal places
        return round(val, 2) if val is not None else None


class MedtrumIOBSensor(MedtrumBaseSensor):
    """Insulin on Board sensor"""

    _attr_unique_id = "medtrum_iob"
    _attr_name = "IOB"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "U"
    _attr_icon = "mdi:insulin-pen"

    def get_value(self):
        return self.coordinator.data.get("iob")

    @property
    def native_value(self):
        val = self.get_value()
        # Round to 2 decimal places
        return round(val, 2) if val is not None else None


class MedtrumLastBolusSensor(MedtrumBaseSensor):
    """Last bolus delivered sensor"""

    _attr_unique_id = "medtrum_last_bolus"
    _attr_name = "Last Bolus"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "U"
    _attr_icon = "mdi:syringe"

    def get_value(self):
        return self.coordinator.data.get("bolus_delivered")

    @property
    def native_value(self):
        val = self.get_value()
        # Round to 2 decimal places
        return round(val, 2) if val is not None else None
