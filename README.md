<!-- ![GeoLocator logo](logo/icon.png) -->

# GeoLocator by SmartyVan
### WHERE are we
**GeoLocator** is a Home Assistant custom integration that retrieves current location and timezone sensor data based on `zone.home` GPS coordinate attributes using one of several provided reverse geocode API options.

### WHEN are we
**Most importantly**, this integration also solves a major problem for mobile Home Assistant servers: it creates a service to update the Home Assistant system timezone programatically. An accurate system timezone is crucial for Automation Timing, Sun events, Template rendering (`now()`, `today_at()`, `as_timestamp()`), and Dashboard time display.

### OFFLINE happens
Designed specifically for moving vehicles (vans, RVs, boats) that *MAY* not always have an internet connection, GeoLocator falls back to a local python library ([timezonefinder](https://pypi.org/project/timezonefinder/)) when no network connection is available. This method is less accurate, but works offline.

*Optionally*: GeoLocator can be used in `Offline` mode to force the use of the local timezonefinderL library at all times to set system timezone — in this mode, no reverse geocode data will be retrived.

---

## 🔧 Installation

### HACS Installation (Custom Repository)

This integration is not yet available in the HACS default store, however you can still install it via HACS as a custom repository:

1. In Home Assistant, go to **HACS → Integrations**
2. Click the **⋮ (three-dot menu)** in the top right
3. Choose **"Custom repositories"**
4. In the dialog:
   - **Repository**: `https://github.com/SmartyVan/hass-geolocator`
   - **Category**: `Integration`
5. Click **Add**

The integration will then appear in your HACS Integrations list and can be installed and updated like any other.

### Or, Manual Installation

1. Copy this repository to your Home Assistant config folder:
   ```
   custom_components/geolocator/
   ```

2. Restart Home Assistant.
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
alias: Update Location Every 5 Minutes
description: ""
triggers:
  - trigger: time_pattern
    minutes: /5
conditions: []
actions:
  - action: geolocator.update_location
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

| Entity | Description |
|:-------|:------------|
| `sensor.geolocator_current_address`* | Formatted location name |
| `sensor.geolocator_city`* | City name |
| `sensor.geolocator_neighborhood`* | Neighborhood name |
| `sensor.geolocator_state`* | State name |
| `sensor.geolocator_country`* | Country name |
| `sensor.geolocator_timezone_id` | Timezone ID (`America/Chicago`) |
| `sensor.geolocator_timezone_abbreviation` | Timezone Abbreviation (`CDT`) |
| `sensor.geolocator_data_source` | API provider used for current data (*or Offline Fallback*)  |

\* *these sensors are only created/updated when using an API*

---

## 🌐 Supported Reverse Geocoding APIs

These are the currently supported APIs. Feel free to submit pull requests for other services.

| API Service        | Credentials Needed      | Notes                        | Formatted Location Name                            |
|--------------------|-------------------------|-----------------------------------------------------------------------|--------|
| **Google Maps**    | API Key | Enable Reverse Geocode & Timezone APIs. Be sure to add billing to your project. Create an [API key](https://developers.google.com/maps). | Full street address |
| **GeoNames**       | Username | Requires free [user account](https://www.geonames.org/login). | Full street address (US only) |
| **BigDataCloud**   | None                 | Free - no API key required. | City, State, Country Only |
| **Offline** | None | **No Reverse Geocode!** Some enclaves or borders are less accurate than the API solutions but works 100% locally using the timezonefinder library. | None |

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
