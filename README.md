HA_Medtrum
Home Assistant custom integration for Medtrum Nanopump systems.

Overview
This integration allows you to monitor your Medtrum Nanopump directly in Home Assistant by reading real-time glucose data, insulin remaining, IOB (Insulin on Board), and other pump metrics.
Tested with: Medtrum Nanopump 200

Features
📊 Real-time Glucose Monitoring - Current blood sugar in mmol/L
💉 Insulin Management - IOB, Remaining Insulin Units, Last Bolus
🔋 Battery Status - CGM Sensor Battery Percentage
📡 Connection Status - Pump connectivity indicator
⏰ Last Update Timestamp - When data was last fetched
📈 Glucose Trend - Rate of change (mmol/L/min)

Sensors Provided
Sensor	Unit	Description
`sensor.medtrum_glucose`	mmol/L	Current blood glucose
`sensor.medtrum_glucose_rate`	mmol/L/min	Glucose trend
`sensor.medtrum_iob`	U	Insulin on Board
`sensor.medtrum_insulin_remaining`	U	Insulin in reservoir
`sensor.medtrum_last_bolus`	U	Last bolus delivered
`sensor.medtrum_sensor_battery`	%	CGM sensor battery
`sensor.medtrum_connection_status`	-	Pump connection state
`sensor.medtrum_last_update`	-	Timestamp of last data fetch

Installation
Via HACS (Recommended)
Open HACS in Home Assistant
Go to Integrations → Click ⋮ → Custom repositories
Add repository: `https://github.com/pdv63/HA_Medtrum`
Category: `Integration`
Click Install
Restart Home Assistant
Manual Installation
Download this repository
Copy the `medtrum` folder to `~/.homeassistant/custom_components/`
Restart Home Assistant
Setup
Go to Settings → Devices & Services
Click Create Integration
Search for Medtrum
Enter your Medtrum account email and password
A 2FA code will be sent to your email - enter it when prompted
✅ Integration is now configured!

Configuration
The integration uses config flow - all settings are configured via the UI.
Scan Interval
Default: 5 minutes (adjust in integration settings)
Reconfigure
To update credentials or rescan:
Go to Devices & Services → Medtrum
Click ⋮ → Reconfigure

Usage Examples
Automations
Alert when glucose is low:
```yaml
automation:
  - alias: "Low Glucose Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.medtrum_glucose
        below: 4
    action:
      - service: notify.mobile_app
        data:
          message: "⚠️ Low glucose: {{ states('sensor.medtrum_glucose') }} mmol/L"
```
Alert when insulin is low:
```yaml
automation:
  - alias: "Low Insulin Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.medtrum_insulin_remaining
        below: 20
    action:
      - service: notify.mobile_app
        data:
          message: "💉 Insulin low: {{ states('sensor.medtrum_insulin_remaining') }} U remaining"
```
Dashboard Card
```yaml
type: entities
entities:
  - entity: sensor.medtrum_glucose
    name: Blood Sugar
  - entity: sensor.medtrum_glucose_rate
    name: Trend
  - entity: sensor.medtrum_iob
    name: Active Insulin
  - entity: sensor.medtrum_insulin_remaining
    name: Reservoir
  - entity: sensor.medtrum_sensor_battery
    name: Sensor Battery
  - entity: sensor.medtrum_connection_status
    name: Connection
title: Medtrum CGM
```

Troubleshooting
Integration not loading
Check Settings → System → Logs for errors
Ensure Home Assistant version is 2023.1 or higher
No data appearing
Wait 5 minutes for first data fetch (default scan interval)
Check credentials are correct
Try Reconfigure to refresh authentication
2FA code expired
If setup fails during 2FA, simply try again
New code is sent automatically
Connection refused (403)
Your session cookies may have expired
Click Reconfigure to log in again

Technical Details
API Base: `https://easyview.medtrum.eu`
Authentication: Email/Password + 2FA via email
Data Update: Every 5 minutes (configurable)
Glucose Unit: mmol/L only (no mg/dL conversion yet)

Development
Requirements
Python 3.8+
Home Assistant 2023.1+
aiohttp (included with Home Assistant)
File Structure
```
medtrum/
├── __init__.py          # Integration setup & coordinator
├── config_flow.py       # Setup flow UI
├── sensor.py            # Sensor definitions
└── manifest.json        # Integration metadata
```
Contributing
Found a bug or want to improve something? Open an issue or PR!
License
MIT License - See LICENSE file for details
Disclaimer
This is an unofficial integration. Use at your own risk. Always verify critical glucose readings with your actual pump display.
Not affiliated with Medtrum or any medical device manufacturer.
Credits
Reverse-engineered using Burp Suite by analyzing the official Medtrum app API.
---
Questions? Open an issue on GitHub!
