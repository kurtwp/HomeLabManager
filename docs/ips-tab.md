# IPs Tab

The **IPs** tab provides a centralized view of every IP address tracked in your home lab — whether discovered automatically via UniFi sync, Nmap scans, or added manually. It supports filtering, tagging, device linking, and detailed per-IP views.

## Accessing the IPs Tab

Click **IPs** in the top navigation bar, or navigate to `/ips`.

## IP Address List

The main view displays all tracked IP addresses as cards, sorted numerically. Each card shows:

- **Status indicator** — 🟢 Active, 🔴 Inactive, ⚪ Unknown
- **IP Address** — in monospace font, clickable to open the detail page
- **Hostname** — resolved or manually entered name
- **Assignment Type** — badge showing STATIC, DHCP, or RESERVED
- **Source** — how the IP was discovered:
  - `UniFi` — synced from UniFi controller (client)
  - `Infra` — UniFi infrastructure device
  - `Nmap` — found via network scan
  - `Manual` — added by hand
- **Tags** — color-coded chips
- **Network name** — which subnet the IP belongs to
- **Last seen** — timestamp of last activity
- **Delete button** — remove with confirmation

### Filtering

Three filters are available and apply automatically when changed:

| Filter | Options |
|--------|---------|
| Network | All Networks, or a specific subnet |
| Status | All, Active, Inactive |
| Tag | All Tags, or a specific tag |

A count of matching IPs is shown above the list (e.g. "47 IPs").

### Adding an IP

Click **Add IP** to open the creation dialog:

| Field | Required | Description |
|-------|----------|-------------|
| IP Address | Yes | The address (e.g. `192.168.1.50`) |
| Network | Yes | Which subnet it belongs to |
| Hostname | No | DNS name or friendly label |
| MAC Address | No | Hardware address (AA:BB:CC:DD:EE:FF) |
| Assignment Type | No | Static, DHCP, or Reserved (defaults to Static) |
| Notes | No | Markdown-formatted notes |

### Deleting IPs

- **Individual** — red trash icon on any IP card (with confirmation)
- **Bulk** — "Delete All" button removes every IP address (changelog history is preserved)

When an IP is deleted:
- Its linked device is also removed if it was the only IP associated with that device (if the device has other IPs, only the IP is deleted)
- Notes attached to the IP are **archived** (not permanently deleted) with the original IP address and hostname stored for future reference
- Archived notes don't appear on newly created IPs but remain in the database for retrieval

## IP Detail Page

Clicking an IP address navigates to `/ips/{id}`, which provides:

### Header
- IP address in large monospace text
- Status badge (Active/Inactive)
- Assignment type badge (Static/DHCP/Reserved)
- Delete button

### Details Panel
- **Hostname** — resolved name
- **MAC Address** — with automatic OUI manufacturer lookup (e.g. "AA:BB:CC:DD:EE:FF (Ubiquiti)")
- **Network** — parent subnet name
- **Last Seen** — when the IP was last active
- **Created** — when the record was first added
- **Device** — linked device name (if any)

### Device Type Assignment
A dropdown lets you assign or change the device type for the IP. This works by:
1. If the IP is already linked to a device, it updates that device's type
2. If not linked, it looks for an existing device matching the MAC or hostname
3. If no matching device exists, it creates a new one automatically

This is a quick way to classify discovered IPs without navigating to the Devices tab.

### Notes
A full Markdown notes editor for recording configuration details, access info, or anything relevant. Notes are saved per-IP.

### Tags
Assign and remove tags for categorization and filtering. Tags are shared across the system (IPs, devices, networks).

## IP Data Model

Each IP address record contains:

| Field | Type | Description |
|-------|------|-------------|
| address | String | The IP address (IPv4 or IPv6) |
| hostname | String | DNS name or manual label |
| mac_address | String | Hardware MAC address |
| assignment_type | Enum | `static`, `dhcp`, or `reserved` |
| status | Enum | `active`, `inactive`, or `unknown` |
| source | String | How it was discovered (`unifi_client`, `unifi_device`, `nmap_scan`, `manual`) |
| notes | Text | Markdown notes |
| last_seen | DateTime | Last time the host responded |
| network_id | FK | Parent network/subnet |
| device_id | FK | Linked device (optional) |

## How IPs Are Populated

IPs can enter the system through several paths:

1. **UniFi Sync** — clients and infrastructure devices discovered from the UniFi controller
2. **Nmap Scan** — hosts found during a network scan
3. **Ping Scan** — quick ICMP sweep results
4. **Manual Entry** — added via the Add IP dialog or the Dashboard quick-add form
5. **Import** — bulk imported via CSV on the Import/Export page

## Relationship to Other Features

- **Networks** — every IP belongs to a network. The network detail page shows all its IPs plus a visual subnet grid.
- **Devices** — IPs can be linked to devices. The device detail page shows all associated IPs.
- **Dashboard** — shows active host count, recently modified IPs, and source breakdown.
- **Tags** — shared tagging system for cross-cutting organization.
- **History** — all IP creates, updates, and deletes are logged in the changelog.
- **Search** — IPs are searchable by address, hostname, or notes content.

## Tips

- Use the Status filter to quickly find inactive/stale IPs that may need cleanup
- The source badges help you understand how each IP was discovered
- Assign device types directly from the IP detail page for quick classification
- MAC address lookups automatically identify the manufacturer — useful for identifying unknown devices
- Use tags like "critical", "IoT", or "guest" to organize IPs across subnets
- Check the Dashboard's "Recently Modified" section to see what's changed lately
