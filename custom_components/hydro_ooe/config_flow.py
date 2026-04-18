"""Config flow for OÖ Hydro Data integration."""
import logging

from homeassistant import config_entries
from homeassistant.helpers import selector
import voluptuous as vol

from .const import DOMAIN, CONF_STATIONS
from .coordinator import HydroOOECoordinator

_LOGGER = logging.getLogger(__name__)


class HydroOOEConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OÖ Hydro Data."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step.

        Args:
            user_input: The input provided by the user.

        Returns:
            The result of the configuration step.
        """
        errors = {}

        # Fetch data to build the selection list.
        coordinator = HydroOOECoordinator(self.hass)
        try:
            data = await coordinator._async_update_data()
        except Exception:
            _LOGGER.exception("Failed to fetch OOE data.")
            return self.async_abort(reason="cannot_connect")

        if not data:
            return self.async_abort(reason="no_stations_found")

        # Format options for the UI.
        select_options = [
            {
                "label": f"{v['attributes']['name']} ({v['attributes']['param']})",
                "value": k,
            }
            for k, v in data.items()
        ]

        if user_input is not None:
            return self.async_create_entry(title="OÖ Hydro Data", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STATIONS): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            multiple=True,
                            options=select_options,
                        )
                    )
                }
            ),
            errors=errors,
        )