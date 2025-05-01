
# GeoLocator

**GeoLocator** is a Home Assistant custom integration that automatically retrieves your current location and timezone based on the `zone.home` GPS coordinates using the Google Maps APIs.  
Designed especially for moving vehicles (vans, RVs, boats), it lets you keep your dashboard up to date — and optionally updates Home Assistant's system timezone automatically.

---

## ✨ Features

- Retrieve and display:
  - Current **City**
  - **Neighborhood**
  - **State**
  - **Formatted Location Address**
  - **Timezone ID** (e.g., `America/Chicago`)
  - **Timezone Name** (e.g., `Central Daylight Time`)
- **Manual update control**: trigger location updates only when needed (no constant polling).
- **Auto-update Home Assistant's timezone** when location timezone changes.
- **Configurable address length** to fit dashboard displays.
- **Works with HACS** for easy installation.

---

## 📦 Installation (via HACS)

1. Add this repository to HACS as a **Custom Repository** (category: Integration).
2. Install **GeoLocator** via HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Integrations** → Add Integration → Search for **GeoLocator**.
5. Enter your **Google Maps API Key** and optional **Max Address Length** setting.

---

## 🛠️ Setup Requirements

- A **Google Cloud API Key** with the following APIs enabled:
  - [Geocoding API](https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com)
  - [Timezone API](https://console.cloud.google.com/apis/library/timezone-backend.googleapis.com)

(Enable billing — both APIs have generous free usage tiers.)

---

## 🔧 Services Provided

| Service | Description |
|:--------|:------------|
| `geolocator.update_location` | Fetch the latest location and timezone from Google APIs, update sensors, and automatically update Home Assistant's timezone if needed. |

Example Automation:
```yaml
- alias: Update GeoLocator When Moving
  trigger:
    - platform: state
      entity_id: device_tracker.your_gps_device
      to: 'not_home'
  action:
    - service: geolocator.update_location
```

---

## ⚙️ Available Sensors

| Entity | Description |
|:-------|:------------|
| `sensor.current_location_formatted` | Formatted location name (neighborhood, city, state, timezone) |
| `sensor.city` | City name |
| `sensor.neighborhood` | Neighborhood name |
| `sensor.state` | State name |
| `sensor.current_timezone` | Timezone ID (`America/Chicago`) |
| `sensor.current_timezone_name` | Timezone full name (`Central Daylight Time`) |

---

## 📋 Notes

- This integration **only updates when manually triggered** — no automatic background polling.
- API costs are minimal, but monitor Google billing if used heavily.
- Intended for users who move frequently across regions and want dashboard and system timezone awareness.

---

## 🧑‍💻 Author

Created by [@SmartyVan](https://github.com/SmartyVan).  
Licensed under MIT License.

---

## 💬 Contributions & Issues

Feel free to open issues, suggest improvements, or contribute pull requests on GitHub!
