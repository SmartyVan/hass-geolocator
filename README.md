<img width="150" alt="GeoLocator" src="https://github.com/SmartyVan/hass-geolocator/blob/main/logo/icon.png?raw=true"/>


# GeoLocator by [SmartyVan](https://www.youtube.com/@SmartyVan)
[![hacs badge](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/v/release/smartyvan/hass-geolocator)](https://github.com/smartyvan/hass-geolocator/releases)

[![Join our Discord](https://img.shields.io/discord/1303421267545821245?label=Join%20Discord&logo=discord)](https://discord.gg/3rqeqES3zP)
[![YouTube](https://img.shields.io/badge/YouTube-Smarty%20Van-red?logo=youtube&logoColor=white)](https://www.youtube.com/@SmartyVan)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-donate-yellow.svg)](https://www.buymeacoffee.com/smartyvan)





### 📺 Watch the [YouTube video](https://www.youtube.com/watch?v=Kg4TQhNOonE) about this project:
[<img width="350" alt="Smarty Van YouTube video" src="https://img.youtube.com/vi/Kg4TQhNOonE/maxresdefault.jpg"/>](https://www.youtube.com/watch?v=Kg4TQhNOonE)
### WHERE are we
**GeoLocator** is a Home Assistant custom integration that retrieves current reverse geocoded location sensor data based on `zone.home` GPS coordinate attributes using one of several provided reverse geocode API options.

### WHEN are we
This integration also solves a major problem for mobile Home Assistant servers: it creates a service to update the Home Assistant system timezone programatically. An accurate system timezone is crucial for Automation Timing, Sun events, Template rendering (`now()`, `today_at()`, `as_timestamp()`), and Dashboard time display.

### OFFLINE happens
Designed specifically for moving vehicles (vans, RVs, boats) that *MAY* not always have an internet connection, GeoLocator falls back to a local python library ([timezonefinder](https://pypi.org/project/timezonefinder/)) when no network connection is available. This method is less accurate, but works offline.

*Optionally*: GeoLocator can be used in `Offline` mode to force the use of the local timezonefinder library at all times to set system timezone — in this mode, no reverse geocode data will be retrived.

---

## 🔧 Installation

### HACS Installation (Custom Repository)

This integration is not yet available in the HACS default store, however you can still install it via [HACS](https://www.hacs.xyz/docs/use/) as a custom repository:

[![Open this repository in your Home Assistant instance.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=SmartyVan&repository=hass-geolocator&category=integration)

1. Click "Open HACS Repository" button above and install GeoLocator
2. Restart Home Assistant
3. Navigate to Settings > Devices & Services
4. Click **Add Integration** at the bottom
5. Search for **GeoLocator**

### Or, Manual Installation

1. Download the source code of the [latest release](https://github.com/SmartyVan/hass-geolocator/releases).
2. Unzip the source code download.
3. Copy **geolocator** from the **custom_components** directory you just downloaded to your Home Assistant **custom_components** directory:
   ```
   config/custom_components/geolocator/
   ```

4. Restart Home Assistant.
---

## 📍 Usage

Basic usage requires two steps:
### Step 1.
Set the GPS coordinate attributes of `zone.home` to your current location using the Home Assistant Core Integration: `homeassistant.set_location` in an automation, script, or developer tools:
```yaml
action: homeassistant.set_location
data:
  latitude: 34.0549
  longitude: -118.2426
```
The source of the coordinates can be from any sensor or input you have available. This may be a router, Home Assistant native iOS / Android app, Cerbo GX with USB GPS dongle, etc.

*Step 1 does not rely on this custom component, but is a necessary step to ensure your `zone.home` has current GPS coordinates.*

### Step 2.
Call custom service: `geolocator.update_location`:
```yaml
action: geolocator.update_location
data: {}
```

This will fetch the Reverse Geocode data and populate sensors (if using an API) and then set the Home Assistant system Timezone if it has changed.

**Example Automation:**\
This is a very basic automation. Consider using conditions to restrict location information udpates only when vehicle is (or has been) moving.
```yaml
alias: "GeoLocator: Update Location"
description: "Fetch Reverse Geocode and Timezone ID from API when zone.home is updated."
triggers:
  - trigger: state
    entity_id:
      - zone.home
conditions: []
actions:
  - action: geolocator.update_location
    metadata: {}
    data: {}
mode: single
```

### 🚨 Important:
By design, this component does **NOT** automatically poll.\
You decide how often you want to update the GPS coordinate attributes of `zone.home`.\
You also decide how often to call `geolocator.update_location`.\
This flexibility allows for maximum control over polling rates, and updates.

---

## ⚙️ Sensors Created

| Entity | Description | Generated by |
|:-------|:------------|:------|
| `sensor.geolocator_current_address`* | Formatted location address | API |
| `sensor.geolocator_city`* | City name | API |
| `sensor.geolocator_state`* | State name | API |
| `sensor.geolocator_country`* | Country name | API |
| `sensor.geolocator_timezone_id` | Timezone ID (`America/Chicago`) | API / Local Fallback |
| `sensor.geolocator_timezone` | Timezone (`Central Daylight Time`) | Local |
| `sensor.geolocator_timezone_abbreviation` | Timezone Abbreviation (`CDT`) | Local |
| `sensor.geolocator_data_source` | API provider used for current data (*or Offline Fallback*)  | Local |
| `sensor.geolocator_plus_code` | Full [Plus Code](https://maps.google.com/pluscodes/) for current location | Local |

\* *these sensors are only created/updated when using an API - they will also be unavailable when GeoLocator falls back to the local Python library*

---

## 🌐 Supported Reverse Geocoding APIs

These are the currently supported APIs. Feel free to submit pull requests for other services.

| Results | API Service | Credentials | Notes | Current Address | Localized |
|:-------:|-------------|-------------|-------|-----------------|:------------:|
|🟢| **Google Maps**    | `API Key` | Enable Reverse Geocode & Timezone APIs. Add billing to your project. Create an [API key](https://developers.google.com/maps). | Full street address | ✔︎ |
|🟢| **OpenCage** | `API Key` | [Sign up](https://opencagedata.com) for a free account and retrieve an API key. \**free accounts can make 2,500 requests/day (1 request/second)* | Full street address | ✔︎ |
|🟡| **GeoNames**       | `Username` | Requires free [user account](https://www.geonames.org/login). After activation, visit [Manage Account](https://www.geonames.org/manageaccount) and enable free web servcies (link at bottom of page).  | Full street address (US only) |
|🟠| **BigDataCloud**   | None                 | Free - no API key required. | City, State, Country Only |
|🟠| **Offline** | None | **No Reverse Geocode!** Some enclaves or borders are less accurate than the API solutions but works 100% locally using the timezonefinder library. | None |

*Only one service is used at a time (with fallback to the local python library). API/user key configuration is available via the UI.*

---

## 🔧 Services Provided

| Service | Description |
|:--------|:------------|
| `geolocator.update_location` | Fetch the latest location and timezone from your chosen API, update sensors, and automatically update Home Assistant's timezone. |
| `geolocator.set_home_timezone` | Used internally by the component to set Home Assistant system timezone using a provided IANA Timezone ID (e.g. `America/New_York`). Can be useful on its own if you acquire your Timezone ID elsewhere and simply need to set system timezone. |

---

## 📋 Notes

- This integration **only updates location and timezone data when manually triggered using the `geolocator.update_location` service** — no automatic background polling.
- API costs are your responsibility, but most services have generous quotas on their free tiers.
- Intended for users who move frequently across regions and want dashboard and system timezone awareness.

---

## 🧑‍💻 Author

Created by [@SmartyVan](https://github.com/SmartyVan).
Smarty Van on [YouTube](https://www.youtube.com/@SmartyVan).\
Licensed under MIT License.

---

## 💬 Contributions & Issues

Feel free to open issues, suggest improvements, or contribute pull requests on GitHub!
