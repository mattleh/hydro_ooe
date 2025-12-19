import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
import logging

from .const import DOMAIN, CONF_STATIONS
from .coordinator import HydroOOECoordinator

_LOGGER = logging.getLogger(__name__)

class HydroOOEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OÖ Hydro Data."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        # 1. Fetch data to build the selection list
        coordinator = HydroOOECoordinator(self.hass)
        try:
            data = await coordinator._async_update_data()
        except Exception:
            _LOGGER.exception("Failed to fetch OOE data")
            return self.async_abort(reason="cannot_connect")

        if not data:
            return self.async_abort(reason="no_stations_found")

        # 2. Format options for the UI
        # We create a list of dicts for the Select Selector
        select_options = [
            {"value": k, "label": f"{v['attributes']['name']} ({v['attributes']['param']})"}
            for k, v in data.items()
        ]

        # 3. Handle Form Submission
        if user_input is not None:
            return self.async_create_entry(
                title="OÖ Hydro Data", 
                data=user_input
            )

        # 4. Show Form with Selector
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_STATIONS): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=select_options,
                        multiple=True,  # Allows selecting multiple stations
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                )
            }),
            errors=errors
        )