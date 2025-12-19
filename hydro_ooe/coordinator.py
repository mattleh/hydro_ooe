import logging
import aiohttp
import async_timeout
from datetime import timedelta,datetime
import zoneinfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, URL, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class HydroOOECoordinator(DataUpdateCoordinator):
    def __init__(self, hass):
        super().__init__(
            hass, _LOGGER, name=DOMAIN, 
            update_interval=timedelta(seconds=UPDATE_INTERVAL)
        )

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(30):
                async with aiohttp.ClientSession() as session:
                    async with session.get(URL) as response:
                        text = await response.text(encoding="ISO-8859-1")
                        _LOGGER.debug("Downloaded ZRXP length: %s", len(text))
                        return self.parse_zrxp(text)
        except Exception as err:
            raise UpdateFailed(f"Error communication with API: {err}")

    def parse_zrxp(self, content):
            """Final refined parser with scoping and timestamp fixes."""
            stations = {}
            segments = content.split('#SANR')
            
            for seg in segments:
                if not seg.strip():
                    continue
                
                seg = "#SANR" + seg
                lines = seg.splitlines()
                metadata = {}
                valid_value = None
                
                # 1. Extract Metadata
                for line in lines:
                    if line.startswith('#'):
                        parts = line.split('|*|')
                        for part in parts:
                            clean = part.replace('#', '').strip()
                            if clean.startswith('SANR'): metadata['id'] = clean[4:]
                            elif clean.startswith('SNAME'): metadata['name'] = clean[5:]
                            elif clean.startswith('CNAME'): metadata['param'] = clean[5:]
                            elif clean.startswith('CUNIT'): metadata['unit'] = clean[5:]
                            elif clean.startswith('SWATER'): metadata['water'] = clean[6:]

                # 2. Find the latest VALID value
                for line in reversed(lines):
                    line = line.strip()
                    if line.startswith('20'):
                        parts = line.split()
                        if len(parts) >= 2:
                            temp_val = parts[1] # Use a temporary variable
                            
                            if temp_val != "-777":
                                valid_value = temp_val
                                raw_ts = parts[0]
                                try:
                                    # UTC Conversion Logic
                                    local_dt = datetime.strptime(raw_ts, "%Y%m%d%H%M%S")
                                    local_dt = local_dt.replace(tzinfo=zoneinfo.ZoneInfo("Europe/Vienna"))
                                    utc_dt = local_dt.astimezone(zoneinfo.ZoneInfo("UTC"))
                                    metadata['timestamp'] = utc_dt.isoformat()
                                except Exception:
                                    metadata['timestamp'] = raw_ts
                                break # Found valid value, exit the inner loop

                # 3. Add to stations
                if 'id' in metadata and valid_value is not None:
                    s_id = metadata['id']
                    param = metadata.get('param', 'Value')
                    key = f"{s_id}_{param}"
                    
                    stations[key] = {
                        "state": valid_value,
                        "attributes": {
                            "name": metadata.get('name', s_id),
                            "param": param,
                            "unit": metadata.get('unit', ''),
                            "water": metadata.get('water', 'N/A'),
                            "measured_at": metadata.get('timestamp', 'N/A')
                        }
                    }
            
            return stations