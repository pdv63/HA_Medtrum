# HA\_Medtrum

Home Assistant custom integration for Medtrum Nanopump systems.

## Overview

This integration allows you to monitor your Medtrum Nanopump directly in Home Assistant by reading real-time glucose data, insulin remaining, IOB (Insulin on Board), and other pump metrics.

**Tested with:** Medtrum Nanopump 200

## Features

* 📊 **Real-time Glucose Monitoring** - Current blood sugar in mmol/L
* 💉 **Insulin Management** - IOB, Remaining Insulin Units, Last Bolus
* 🔋 **Battery Status** - CGM Sensor Battery Percentage
* 📡 **Connection Status** - Pump connectivity indicator
* ⏰ **Last Update Timestamp** - When data was last fetched
* 📈 **Glucose Trend** - Rate of change (mmol/L/min)

## Sensors Provided

|Sensor|Unit|Description|
|-|-|-|
|`sensor.medtrum\_glucose`|mmol/L|Current blood glucose|
|`sensor.medtrum\_glucose\_rate`|mmol/L/min|Glucose trend|
|`sensor.medtrum\_iob`|U|Insulin on Board|
|`sensor.medtrum\_insulin\_remaining`|U|Insulin in reservoir|
|`sensor.medtrum\_last\_bolus`|U|Last bolus delivered|
|`sensor.medtrum\_sensor\_battery`|%|CGM sensor battery|
|`sensor.medtrum\_connection\_status`|-|Pump connection state|
|`sensor.medtrum\_last\_update`|-|Timestamp of last data fetch|

## Installation

### Via HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Go to **Integrations** → Click **⋮** → **Custom repositories**
3. Add repository: `https://github.com/pdv63/HA\_Medtrum`
4. Category: `Integration`
5. Click **Install**
6. **Restart Home Assistant**

### Manual Installation

1. Download this repository
2. Copy the `medtrum` folder to `\~/.homeassistant/custom\_components/`
3. **Restart Home Assistant**

## Setup

1. Go to **Settings → Devices \& Services**
2. Click **Create Integration**
3. Search for **Medtrum**
4. Enter your Medtrum account **email** and **password**
5. A 2FA code will be sent to your email - enter it when prompted
6. ✅ Integration is now configured!

## Configuration

The integration uses **config flow** - all settings are configured via the UI.

### Scan Interval

Default: **5 minutes** (adjust in integration settings)

### Reconfigure

To update credentials or rescan:

* Go to **Devices \& Services → Medtrum**
* Click **⋮** → **Reconfigure**

## Usage Examples

### Automations

**Alert when glucose is low:**

```yaml
automation:
  - alias: "Low Glucose Alert"
    trigger:
      - platform: numeric\_state
        entity\_id: sensor.medtrum\_glucose
        below: 4
    action:
      - service: notify.mobile\_app
        data:
          message: "⚠️ Low glucose: {{ states('sensor.medtrum\_glucose') }} mmol/L"
```

**Alert when insulin is low:**

```yaml
automation:
  - alias: "Low Insulin Alert"
    trigger:
      - platform: numeric\_state
        entity\_id: sensor.medtrum\_insulin\_remaining
        below: 20
    action:
      - service: notify.mobile\_app
        data:
          message: "💉 Insulin low: {{ states('sensor.medtrum\_insulin\_remaining') }} U remaining"
```

### Dashboard Card

```yaml
type: entities
entities:
  - entity: sensor.medtrum\_glucose
    name: Blood Sugar
  - entity: sensor.medtrum\_glucose\_rate
    name: Trend
  - entity: sensor.medtrum\_iob
    name: Active Insulin
  - entity: sensor.medtrum\_insulin\_remaining
    name: Reservoir
  - entity: sensor.medtrum\_sensor\_battery
    name: Sensor Battery
  - entity: sensor.medtrum\_connection\_status
    name: Connection
title: Medtrum CGM
```

## Troubleshooting

### Integration not loading

* Check **Settings → System → Logs** for errors
* Ensure Home Assistant version is 2023.1 or higher

### No data appearing

* Wait 5 minutes for first data fetch (default scan interval)
* Check credentials are correct
* Try **Reconfigure** to refresh authentication

### 2FA code expired

* If setup fails during 2FA, simply try again
* New code is sent automatically

### Connection refused (403)

* Your session cookies may have expired
* Click **Reconfigure** to log in again

## Technical Details

* **API Base:** `https://easyview.medtrum.eu`
* **Authentication:** Email/Password + 2FA via email
* **Data Update:** Every 5 minutes (configurable)
* **Glucose Unit:** mmol/L only (no mg/dL conversion yet)


Development
---

### Requirements

* Python 3.8+
* Home Assistant 2023.1+
* aiohttp (included with Home Assistant)

### File Structure

```
medtrum/
├── \_\_init\_\_.py          # Integration setup \& coordinator
├── config\_flow.py       # Setup flow UI
├── sensor.py            # Sensor definitions
└── manifest.json        # Integration metadata
```

## Contributing

Found a bug or want to improve something? Open an issue or PR!

## License

MIT License - See LICENSE file for details

## Disclaimer

This is an unofficial integration. Use at your own risk. Always verify critical glucose readings with your actual pump display.

**Not affiliated with Medtrum or any medical device manufacturer.**

## Credits

Reverse-engineered using Burp Suite by analyzing the official Medtrum app API.

\---

**Questions?** Open an issue on GitHub!

