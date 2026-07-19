# Devices Tab

The **Devices** tab lets you manage all physical and virtual devices in your home lab — servers, switches, access points, printers, and anything else on your network. It supports categorization by type, tagging, filtering, and links devices to their IP addresses.

## Accessing the Devices Tab

Click the **Devices** dropdown in the top navigation bar. The menu shows:

- **All Devices** — full device list (`/devices`)
- **Per-type categories** — dynamically lists device types that have at least one device, with a count (e.g. "Switch (3)")
- **Unclassified** — devices without an assigned type
- **Manage Device Types** — create and edit device categories (`/device-types`)

## Device List

The main devices page displays all devices as cards. Each card shows:

- **Icon** — based on the device type's configured Material icon
- **Name** — clickable to open the device detail page
- **Device Type** — shown as a badge (e.g. "Switch", "Access Point")
- **Tags** — color-coded chips for organization
- **IP Addresses** — up to two associated IPs shown inline, with a "+N more" indicator
- **Manufacturer and Model** — displayed when available
- **IP count badge** — total number of IPs linked to the device

### Filtering

Two filter dropdowns are available above the list:

| Filter | Purpose |
|--------|---------|
| Device Type | Show only devices of a specific type |
| Tag | Show only devices with a specific tag |

URL-based category filtering is also supported. Navigating from the Devices dropdown menu pre-filters the list (e.g. `/devices?category=type_5`).

### Adding a Device

Click **Add Device** to open the creation dialog:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly device name |
| Device Type | No | Category (Switch, Server, AP, etc.) |
| Manufacturer | No | e.g. Ubiquiti, HP, Dell |
| Model | No | e.g. USW-Pro-48-PoE |
| Serial Number | No | Hardware serial |
| MAC Address | No | Validated format (AA:BB:CC:DD:EE:FF) |
| Notes | No | Free-text notes |

### Deleting Devices

- **Individual** — click the red trash icon on any device card (with confirmation)
- **Bulk** — the "Delete All" button removes every device (with confirmation warning)

When a device is deleted, its notes are archived with the original device name for future reference. Archived notes don't appear on other devices but remain searchable.

## Device Detail Page

Clicking a device name navigates to `/devices/{id}`, which provides a full view:

### Details Panel
- Manufacturer, Model, Serial Number, MAC address
- Creation timestamp
- All associated IP addresses (clickable links to IP detail pages)

### UniFi Device Health (Ubiquiti devices only)
For devices with manufacturer "Ubiquiti" and a MAC address, live health stats are fetched:
- **Uptime** — how long the device has been running
- **CPU** — usage percentage with color-coded progress bar
- **RAM** — usage with used/total MB breakdown
- **Load Average** — 1/5/15 minute load
- **Temperature** — per-sensor readings (when available)
- **PoE Power** — total wattage used vs max, plus a per-port breakdown table showing connected device, power draw, voltage, current, and PoE class

### Notes
A full notes editor for recording maintenance info, configuration details, or anything relevant to the device.

### Tags
Assign and remove tags for categorization. Tags are shared across devices, networks, and IPs.

### Physical Location
Track where the device lives physically:
- **Location** — room or building
- **Rack Position** — rack unit (e.g. "U12")
- **Shelf** — shelf label

### Custom Fields
Any custom fields defined for the "device" entity type are shown and editable here.

## Device Types

Accessed via **Devices → Manage Device Types** (`/device-types`), this page lets you define the categories used to classify devices.

Each device type has:

| Field | Description |
|-------|-------------|
| Name | Category name (e.g. "Firewall", "NAS", "Camera") |
| Icon | Material icon name (browse at fonts.google.com/icons) |
| Description | Optional explanation of the type |

Actions:
- **Add Type** — create a new category
- **Edit** — change name, icon, or description
- **Delete** — removes the type; devices using it become "unclassified"

## How Devices Relate to Other Data

- **IP Addresses** — a device can have multiple IPs linked to it. These show on the device detail page and the IP list.
- **Tags** — shared tag system across devices, networks, and IPs for unified filtering.
- **UniFi Sync** — when syncing from UniFi, discovered infrastructure devices (APs, switches, gateways) are automatically created or updated in the devices list.
- **Dashboard** — the main dashboard shows separate counts for UniFi devices vs other devices.
- **Custom Fields** — extend the device model with any additional fields you need.

## Tips

- Use device types to organize by function (networking, compute, storage, IoT, etc.)
- Assign meaningful icons to device types for quick visual identification
- Link devices to their IPs for a complete network inventory
- Use tags for cross-cutting concerns like "critical", "needs-upgrade", or location-based grouping
- The physical location fields help when you need to find a device in a rack or closet
