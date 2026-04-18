"""DataUpdateCoordinator for the OÖ Hydro Data integration."""
import logging
from datetime import datetime, timezone, timedelta

import async_timeout
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL, URL

_LOGGER = logging.getLogger(__name__)


class HydroOOECoordinator(DataUpdateCoordinator):
    """Class to manage fetching OÖ Hydro data."""

    def __init__(self, hass):
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from the ZRXP file."""
        try:
            async with async_timeout.timeout(30):
                session = async_get_clientsession(self.hass)
                async with session.get(URL) as response:
                    text = await response.text(encoding="ISO-8859-1")
                    _LOGGER.debug("Downloaded ZRXP length: %s", len(text))
                    return self.parse_zrxp(text)
        except Exception as err:
            raise UpdateFailed(f"Error communication with API: {err}") from err

    def parse_zrxp(self, content):
        """Parse the ZRXP content into a structured dictionary.

        Args:
            content (str): The raw string content of the ZRXP file.

        Returns:
            dict: A dictionary of station data keyed by station ID and parameter.
        """
        stations = {}
        segments = content.split("#SANR")

        for seg in segments:
            if not seg.strip():
                continue

            seg = f"#SANR{seg}"
            lines = seg.splitlines()
            metadata = {}
            valid_value = None

            # Extract metadata from headers.
            for line in lines:
                if line.startswith("#"):
                    parts = line.split("|*|")
                    for part in parts:
                        clean = part.replace("#", "").strip()
                        if clean.startswith("CNAME"):
                            metadata["param"] = clean[5:].strip()
                        elif clean.startswith("CUNIT"):
                            metadata["unit"] = clean[5:].strip()
                        elif clean.startswith("RINVAL"):
                            metadata["rinval"] = clean[6:].strip()
                        elif clean.startswith("SANR"):
                            metadata["id"] = clean[4:].strip()
                        elif clean.startswith("SNAME"):
                            metadata["name"] = clean[5:].strip()
                        elif clean.startswith("SWATER"):
                            metadata["water"] = clean[6:].strip()
                        elif clean.startswith("TZ"):
                            metadata["tz"] = clean[2:].strip()

            # Find the latest valid value.
            header_rinval = metadata.get("rinval", "-777")
            header_tz = metadata.get("tz", "UTC+1")

            # Parse offset from TZ header, e.g., "UTC+1" -> 1 hour.
            offset_hours = 0
            if "UTC" in header_tz:
                try:
                    offset_str = header_tz.replace("UTC", "").strip()
                    if offset_str:
                        offset_hours = int(offset_str)
                except ValueError:
                    _LOGGER.warning(
                        "Could not parse offset from TZ header: %s", header_tz
                    )

            tz_info = timezone(timedelta(hours=offset_hours))

            for line in reversed(lines):
                line = line.strip()
                if line and line[0].isdigit():
                    parts = line.split()
                    if len(parts) >= 2:
                        raw_ts, val_str = parts[0], parts[1]
                        if val_str != header_rinval:
                            try:
                                if len(raw_ts) >= 14:
                                    dt = datetime.strptime(raw_ts[:14], "%Y%m%d%H%M%S")
                                elif len(raw_ts) >= 12:
                                    dt = datetime.strptime(raw_ts[:12], "%Y%m%d%H%M")
                                else:
                                    continue

                                # Apply offset and convert to UTC.
                                dt = dt.replace(tzinfo=tz_info)
                                metadata["timestamp"] = dt.astimezone(timezone.utc)
                                valid_value = float(val_str)
                                break
                            except (ValueError, TypeError):
                                continue

            # Add valid data to stations dictionary.
            if "id" in metadata and valid_value is not None:
                s_id = metadata["id"]
                param = metadata.get("param", "Value")
                key = f"{s_id}_{param}"

                stations[key] = {
                    "attributes": {
                        "measured_at": metadata.get("timestamp", "N/A"),
                        "name": metadata.get("name", s_id),
                        "param": param,
                        "unit": metadata.get("unit", ""),
                        "water": metadata.get("water", "N/A"),
                    },
                    "state": valid_value,
                }

        return stations