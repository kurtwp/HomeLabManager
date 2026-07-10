# Tools Menu (Wrench Icon)

The **wrench icon** (🔧) in the top-right corner of the navigation bar opens a dropdown menu with utility tools for your home lab. These are supplementary features that don't fit neatly into the main navigation tabs.

## Menu Items

| Item | Route | Purpose |
|------|-------|---------|
| Calculator | `/calculator` | IP subnet calculator |
| Reports | `/reports` | Charts and analytics |
| Locations | `/locations` | Physical device location tracking |
| Custom Fields | `/custom-fields` | Extend entity data with custom attributes |
| Notifications | `/notifications` | Alert settings, test, and history |
| Settings | `/settings` | Edit .env configuration from the UI |

---

## Calculator

A full-featured IP subnet calculator with three tools in tabbed view:

### Subnet Calculator

Enter a CIDR notation (IPv4 or IPv6) and get:

- Network address and broadcast address
- Netmask and host mask
- Prefix length
- Total addresses and usable hosts
- First and last host addresses
- Network class (A/B/C/D/E) for IPv4
- Whether the network is private or public

**Example:** Enter `192.168.1.0/24` to see that it has 254 usable hosts, first host 192.168.1.1, last host 192.168.1.254.

### Subnet Splitter

Split a large network into smaller subnets by specifying a new prefix length.

- Enter the parent network CIDR
- Enter the desired new prefix length
- View a table of all resulting subnets with their first/last hosts and usable count

**Example:** Split `10.0.0.0/16` into `/24` subnets to get 256 subnets of 254 hosts each.

### IP-in-Subnet Checker

Verify whether a specific IP address falls within a given subnet.

- Enter an IP address and a subnet CIDR
- Get a clear green (yes) or red (no) result

**Example:** Check if `192.168.1.50` is in `192.168.1.0/24` → ✅ Yes.

---

## Reports

Visual analytics and charts about your infrastructure at `/reports`:

### Subnet Utilization Chart

A stacked bar chart showing used vs free IPs across all networks. Gives a quick visual of which subnets are running out of space.

### Capacity Warnings

Lists any networks above 80% utilization with:
- Network name and CIDR
- Usage percentage and IP counts
- Color-coded progress bars (orange at 80%, red at 95%)

If all networks are below 80%, a green "all clear" message is shown.

### Device Type Distribution

A pie chart showing how many devices exist in each device type category (Switch, AP, Server, etc.), including an "Unclassified" slice for devices without a type.

### Recent Scan Activity

A table of the 10 most recent network scans showing:
- Network scanned
- When it ran
- Scan type
- Hosts found and added
- Duration

---

## Locations

A physical location overview page at `/locations` that answers "where are my devices?"

### Summary Stats

Four cards at the top:
- Total devices
- Located (have at least one location field set)
- No location set (missing all location fields)
- Number of distinct locations

### Location Groups

Devices are grouped by their `location` field value. Each group shows:
- Location name with device count badge
- Table of devices at that location with rack position, shelf, type, and MAC
- Device names are clickable links to their detail pages

### Devices Without Location

Lists devices that have no location, rack, or shelf set, with a "Set Location" button linking to their detail page for quick assignment.

---

## Custom Fields

Extend the data model without code changes at `/custom-fields`.

### What Are Custom Fields?

Custom fields let you add arbitrary attributes to IPs, devices, or networks beyond the built-in fields. Useful for tracking things like purchase dates, warranty info, department ownership, or anything specific to your environment.

### Field Types

| Type | Description |
|------|-------------|
| Text | Free-form text input |
| Number | Numeric input |
| Date | Date string (YYYY-MM-DD) |
| Select | Dropdown with predefined choices |
| Checkbox | Boolean toggle |

### Creating a Custom Field

Click **New Field** and configure:

| Setting | Description |
|---------|-------------|
| Field Name | Label shown on entity detail pages |
| Field Type | Text, Number, Date, Select, or Checkbox |
| Entity Type | Which entities get this field: IP, Device, or Network |
| Options | Comma-separated choices (for Select type only) |
| Default Value | Pre-filled value (optional) |
| Required | Whether the field must be filled |

### Where Custom Fields Appear

Custom fields show up automatically on the detail pages of the entity type they're assigned to:
- IP detail page → fields with entity type "IP"
- Device detail page → fields with entity type "Device"
- Network detail page → fields with entity type "Network"

Each detail page shows a "Custom Fields" card with the configured inputs and a Save button.

### Managing Fields

The main Custom Fields page shows a table of all defined fields, filterable by entity type. Each field can be deleted (the field definition and all stored values are removed).

---

## Settings

A UI-based editor for the `.env` configuration file at `/settings`. Eliminates the need to SSH into the server or manually edit files for common configuration changes.

### How It Works

The Settings page reads the current `.env` file and presents all configuration options as a form. When you save, it writes the values back to `.env` while preserving comments and formatting.

A restart is required for most changes to take effect (the app reads `.env` at startup).

### Configuration Groups

| Group | What It Configures |
|-------|-------------------|
| Application | App title, port, database URL |
| UniFi Integration | API keys, base URL, site ID |
| Notifications — General | Master enable/disable toggle |
| Notifications — Email | SMTP server, credentials, recipients |
| Notifications — Webhook | Webhook URL and enable toggle |
| Notifications — Pushover | App token and user key |

### Field Types

- **Text** — standard text input
- **Password** — masked input with show/hide toggle (for API keys and credentials)
- **Number** — numeric input (e.g. port numbers)
- **Toggle** — on/off switch for boolean settings (true/false)

### Actions

- **Save Settings** — writes all values to the `.env` file
- **Reset** — reverts the form to the last saved values (discards unsaved changes)

### Security Notes

- The Settings page is accessible to anyone who can reach the app — consider this if exposing the app outside your LAN
- API keys and passwords are stored in plain text in `.env` (standard for self-hosted apps)
- The `.env` file is excluded from git via `.gitignore`

### What Takes Effect Immediately vs Requires Restart

| Setting Group | Restart Needed? |
|---------------|----------------|
| Notifications (all channels) | No — takes effect immediately |
| Application (title, port, database) | Yes |
| UniFi Integration (API keys, URLs) | Yes |

---

## Tips

- Use the Calculator before creating networks to plan your addressing
- Check Reports periodically to catch subnets that are running low on space
- The Locations page is great for generating a quick physical inventory map
- Custom fields are powerful for tracking site-specific metadata without modifying code
- Configure Notifications to get alerted when hosts go down or firmware updates are available
- Use Settings to configure .env without needing SSH or terminal access
- All tools in this menu are read-only or configuration-only — they don't modify your core network/IP/device data
