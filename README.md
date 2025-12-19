# OÖ Hydro Data for Home Assistant

This custom integration fetches real-time hydrological data (water level, discharge, temperature) from the **Land Oberösterreich (Hydrographischer Dienst)** open data portal.



## Features
- **Real-time Monitoring:** Collects data directly from the official `.zrxp` export.
- **Smart Filtering:** Automatically ignores invalid `-777` measurement markers and finds the latest valid data point.
- **Timezone Aware:** Converts local Austrian time (CET/CEST) to UTC for perfect Home Assistant history graphs.
- **Easy Setup:** Fully configurable via the Home Assistant UI (Config Flow)—no YAML required.
- **Attribute Rich:** Includes metadata such as the water body name and the exact measurement timestamp.

## Installation

### Method 1: HACS (Recommended)
1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Go to **HACS** > **Integrations** > **Three dots (top right)** > **Custom Repositories**.
3. Paste the URL of this repository.
4. Select **Integration** as the category and click **Add**.
5. Find "OÖ Hydro Data" in HACS and click **Download**.
6. Restart Home Assistant.

### Method 2: Manual
1. Download the `hydro_ooe` folder from this repository.
2. Copy the folder to your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration
1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **OÖ Hydro Data**.
3. A list of available measuring stations will appear. Select the ones you wish to track.
4. Click **Submit**.

## Data Source
Data is provided by [data.ooe.gv.at](https://data.ooe.gv.at/) under the Creative Commons Attribution 4.0 International license.

## Disclaimer
This integration is not an official product of the State of Upper Austria. It is a community-driven project using public data.
