from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CONF_STATIONS

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selected_ids = entry.data[CONF_STATIONS]
    
    # Create entities only if they exist in the coordinator's current data
    entities = []
    for station_id in selected_ids:
        if station_id in coordinator.data:
            entities.append(HydroStationSensor(coordinator, station_id))
        else:
            # This helps debug if you selected a station that isn't in the file
            import logging
            _LOGGER = logging.getLogger(__name__)
            _LOGGER.warning("Station %s not found in data file", station_id)
    
    async_add_entities(entities)

class HydroStationSensor(CoordinatorEntity, SensorEntity):
    """Representation of an OÖ Hydro Sensor."""

    def __init__(self, coordinator, station_id):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.station_id = station_id
        
        # Pull initial metadata
        meta = self.coordinator.data[self.station_id]['attributes']
        self._attr_name = f"Hydro {meta.get('name')} {meta.get('param')}"
        
        # Clean Unique ID (must be unique and lower_case_with_underscores)
        clean_id = station_id.lower().replace(" ", "_").replace(".", "_")
        self._attr_unique_id = f"hydro_ooe_{clean_id}"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Grab the latest value from the coordinator data dict
        data = self.coordinator.data.get(self.station_id)
        if data:
            return data["state"]
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit."""
        return self.coordinator.data[self.station_id]['attributes'].get('unit')

    @property
    def extra_state_attributes(self):
        """Return metadata for the station."""
        return self.coordinator.data[self.station_id]['attributes']