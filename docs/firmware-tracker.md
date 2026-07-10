# Firmware Tracker

The **Firmware Tracker** monitors firmware versions across your UniFi network devices and alerts you when updates are available.

## Accessing the Firmware Tracker

Click the **Discovery** dropdown → **Firmware Tracker**, or navigate to `/firmware`.

## Overview

The firmware page shows:

- **Summary cards** — total devices tracked, up-to-date count, updates available count
- **Updates Available** — highlighted cards for devices with pending firmware updates, showing current vs available version
- **Up to Date** — table of devices running the latest firmware with last-checked timestamps
- **Unknown Firmware** — devices where the firmware version couldn't be determined

## How It Works

1. The tracker pulls device data from the UniFi Integration API (`/sites/{siteId}/devices`)
2. It extracts the current firmware version and any available upgrade information
3. Each device is tracked by MAC address in a local database table
4. When a new update is detected that wasn't there before, a notification is sent
5. The check runs automatically every 6 hours via the background scheduler

### Data Pulled from UniFi

The tracker reads these fields from the device API response:

| Field | Purpose |
|-------|---------|
| `firmwareVersion` / `version` | Current running firmware |
| `upgradeToFirmware` / `upgradableFirmwareVersion` | Available update version |
| `upgradeState` | Whether an upgrade is pending |
| `upgradable` / `isUpgradable` | Boolean upgrade flag |
| `mac` | Unique device identifier |
| `name` / `hostname` | Device name |
| `model` | Hardware model |

## Manual Check

Click the **Check for Updates** button to run an immediate firmware scan. The results show:

- How many devices were checked
- How many have updates available
- Any errors encountered

## Automatic Checks

The firmware checker runs as a background job every 6 hours via APScheduler. No configuration needed — it starts automatically with the application.

You can see the scheduled job in the **Scheduled Scans** page (`/scheduler`).

## Notifications

When a firmware update is newly detected (wasn't flagged on the previous check), an alert is sent through all enabled notification channels with:

- Device name
- Current firmware version
- Available firmware version

This only fires once per update — you won't get repeated alerts for the same pending update.

See the [Notifications](notifications) documentation for channel configuration.

## Requirements

- UniFi Integration must be configured (`UNIFI_API_KEY`, `UNIFI_BASE_URL`, `UNIFI_SITE_ID` in `.env`)
- The API key needs read access to the devices endpoint
- Works with UDM, UDM Pro, UDM SE, and any UniFi controller exposing the Integration API

## Data Stored

Each tracked device stores:

| Field | Description |
|-------|-------------|
| Device MAC | Unique identifier (used as key) |
| Device Name | Friendly name from UniFi |
| Model | Hardware model string |
| Current Version | Running firmware version |
| Available Version | Upgrade version (if any) |
| Update Available | Boolean flag |
| Last Checked | When the last scan ran |
| Last Updated | When the firmware version changed |

## Tips

- Run a manual check after upgrading devices to verify the tracker clears the update flag
- The tracker is read-only — it doesn't initiate upgrades, only reports on availability
- If a device shows "Unknown Firmware", it may be offline or the API response format differs
- Pair with uptime monitoring to ensure devices come back after firmware updates
- Check the firmware page before and after controller upgrades to track what changed
