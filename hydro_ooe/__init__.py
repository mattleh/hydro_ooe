from .const import DOMAIN
from .coordinator import HydroOOECoordinator

async def async_setup_entry(hass, entry):
    coordinator = HydroOOECoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True