# Networks Tab

The **Networks** tab is the central place to manage all your network subnets and VLANs. It provides a complete view of your IP address space, utilization tracking, and quick access to scanning and network details.

## Accessing the Networks Tab

Click **Networks** in the top navigation bar, or navigate to `/networks`.

## Features

### Network List

The main view displays all configured networks as cards, each showing:

- **Name** — a friendly label for the network (e.g. "Main LAN", "IoT VLAN")
- **CIDR** — the subnet in CIDR notation (e.g. `192.168.1.0/24`)
- **VLAN ID** — displayed as a badge when assigned
- **Tags** — color-coded tag chips for categorization
- **Description** — optional notes shown below the CIDR
- **Utilization** — percentage and count of used vs total IPs

### Adding a Network

Click the **Add Network** button to open the creation dialog. Fields include:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly name for the network |
| CIDR | Yes | Subnet in CIDR notation (e.g. `10.0.0.0/24`) |
| VLAN ID | No | VLAN tag (1–4094) |
| Gateway | No | Default gateway IP |
| DNS Servers | No | Comma-separated DNS servers |
| Description | No | Free-text description |
| DHCP Start | No | Start of DHCP range — used to auto-classify IPs |
| DHCP End | No | End of DHCP range |

The DHCP range is used during scans to automatically classify discovered IPs as either Static or DHCP based on whether they fall within the defined range.

### Tag Filtering

Use the **Filter by Tag** dropdown to narrow the network list to only those with a specific tag applied. This is useful when managing many networks across different locations or purposes.

### Per-Network Actions

Each network card has action buttons on the right:

- **Scan** (radar icon) — runs a network scan (ping sweep) against the subnet, discovers new hosts, and marks missing ones as inactive
- **View Details** (eye icon) — opens the network detail page showing all IPs, the subnet grid, and network-specific settings
- **Delete** (trash icon) — removes the network and all associated IP addresses (with confirmation)

### Bulk Delete

The **Delete All** button removes every network and all associated IPs. A confirmation dialog warns that this cannot be undone.

## Network Detail Page

Clicking **View Details** on a network card navigates to `/networks/{id}`, which shows:

- Full IP address table for the subnet
- Visual **subnet grid** — a color-coded grid showing allocation at a glance (free, static, DHCP, reserved, inactive)
- Network metadata (gateway, DNS, DHCP range, VLAN)
- Ability to edit network properties
- Refresh hostnames via reverse DNS lookup

## Utilization Tracking

Each network shows real-time utilization calculated as:

```
used IPs / (total addresses - 2) × 100%
```

The total excludes the network and broadcast addresses. This utilization is also shown on the Dashboard in the **Network Utilization** section with progress bars.

## Integration with Scans

Networks are the primary target for discovery scans:

- **Ping Scan** — quick ICMP sweep of the subnet
- **Nmap Scanner** — detailed port/service scanning
- **Scheduled Scans** — automated recurring scans via the scheduler

When a scan completes, newly discovered hosts are added as IP entries under the network, and hosts that no longer respond are marked inactive.

## Tips

- Define DHCP ranges to get automatic static/DHCP classification on scan results
- Use tags to group networks by location, function, or environment
- Check the Dashboard for a quick overview of utilization across all networks
- The subnet grid on the detail page gives an instant visual of where free space exists
