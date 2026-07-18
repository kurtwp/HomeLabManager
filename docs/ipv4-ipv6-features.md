# IPv4 and IPv6 Features

This document outlines how the Home Lab Manager handles IPv4 and IPv6 address management.

---

## Feature Comparison

| Feature | IPv4 | IPv6 | Notes |
|---------|:----:|:----:|-------|
| Subnet & Section Hierarchy | ✅ | ✅ | Nested networks, VLANs, parent-child relationships |
| Visual Subnet Display | ✅ | — | Color-coded grid (IPv4 only, /24 or smaller) |
| Free Space Calculation | ✅ | ✅ | Automatic used/free/total with utilization percentage |
| Subnet Calculator | ✅ | ✅ | Calculate, split, and check membership for both protocols |
| Database Search | ✅ | ✅ | Full-text search across addresses, MACs, hostnames, notes |
| Custom Fields | ✅ | ✅ | User-defined metadata on any IP, device, or network |
| Static/DHCP Classification | ✅ | ✅ | DHCP range-based assignment type detection |
| Network Scanning (Nmap/Ping) | ✅ | ⚠️ | Works if targets are reachable; nmap supports IPv6 with `-6` flag |
| SNMP Discovery | ✅ | ✅ | Queries by IP address regardless of protocol |
| Tags & Labels | ✅ | ✅ | Color-coded tags on IPs, devices, networks |
| Change History | ✅ | ✅ | Full audit trail for all entities |
| CSV Import/Export | ✅ | ✅ | Supports any address format in the `address` field |
| Notes (Multi-titled) | ✅ | ✅ | Markdown notes with timestamps on any IP |

---

## IPv4 Features (Full Support)

### Subnet & Section Hierarchy

Networks are organized with:
- **Name and CIDR** (e.g., "Main LAN" — `192.168.2.0/24`)
- **VLAN ID** for logical grouping
- **Parent-child nesting** via `parent_id` for subdivided subnets
- **Description and notes** per network

Navigate: **Networks** in the nav bar.

### Visual Subnet Display

Each IPv4 network detail page shows a **color-coded IP allocation grid**:
- 🟢 **Green** — Free (available)
- 🔵 **Blue** — Static assignment
- 🟠 **Orange** — DHCP assignment
- ⚫ **Gray** — Reserved
- 🔴 **Red** — Inactive (previously seen, now offline)

Each cell shows the last octet and has a hover tooltip with hostname and assignment type.

Navigate: **Networks** → click a network → "Subnet Map" section.

### Free Space Calculation

Displayed on network detail pages:
- Total addresses in the subnet
- Used addresses (tracked IPs)
- Free addresses (unallocated)
- Utilization percentage with progress bar
- Color changes to red when utilization exceeds 80%

### Subnet Calculator

Available at **Tools** (wrench icon) → **Calculator**:

**Subnet Calculator tab:**
- Input any CIDR notation (e.g., `192.168.1.0/24`)
- Outputs: network address, broadcast, netmask, host mask, prefix length, total addresses, usable hosts, first/last host, network class, private status

**Subnet Splitter tab:**
- Input a network CIDR and a new prefix length
- Splits into smaller subnets with a table showing each subnet, first/last host, and usable host count

**IP-in-Subnet Checker tab:**
- Input an IP address and a subnet CIDR
- Visual pass/fail indicator showing whether the IP belongs to the subnet

### DHCP Range Configuration

Each network can have a DHCP range defined:
- **DHCP Start** and **DHCP End** addresses
- IPs within the range are classified as DHCP
- IPs outside the range are classified as Static
- Used by scans and UniFi sync to auto-classify discovered IPs

Navigate: **Networks** → click a network → "DHCP Range" section.

### Database Search

The header search bar searches across:
- IP addresses (exact or partial match)
- MAC addresses
- Hostnames
- Device names
- Notes content
- Documentation articles

Navigate: Type in the **Search** box in the header bar, press Enter.

### Custom Fields

User-defined metadata fields:
- Types: Text, Number, Date, Select (dropdown), Checkbox
- Assignable to: IPs, Devices, or Networks
- Fields are managed at **Tools** → **Custom Fields**
- Values are shown and editable on device detail pages

---

## IPv6 Features (Supported)

### Adding IPv6 Networks

IPv6 networks are added the same way as IPv4:
1. Go to **Networks** → **Add Network**
2. Enter a name and IPv6 CIDR (e.g., `2001:db8::/48` or `fd00::/64`)
3. Set VLAN, gateway, DNS as needed

The application uses Python's `ipaddress` module which natively handles both IPv4 and IPv6.

### IPv6 Subnet Calculator

The calculator page fully supports IPv6:
- Input `2001:db8::/32` → get network info, total addresses, etc.
- Split `2001:db8::/48` into `/64` subnets
- Check if `2001:db8::1` is in `2001:db8::/32`

### IPv6 Limitations

| Limitation | Reason |
|-----------|--------|
| No visual subnet grid | IPv6 address space is too large for a grid (a /64 has 18 quintillion addresses) |
| Scan discovery | Nmap IPv6 scanning requires the `-6` flag and specific targets; ping sweep of entire IPv6 subnets is impractical |
| DHCP range classification | DHCPv6/SLAAC ranges can be configured manually in the DHCP range fields |

### IPv6 Best Practices in This App

1. **Use /64 networks** — standard subnet size for IPv6
2. **Add specific hosts** — rather than scanning, manually add or import known IPv6 addresses
3. **Use the calculator** — for subnet math and splitting
4. **Tags and notes** — work identically for IPv6 addresses
5. **CSV import** — bulk import IPv6 addresses from a spreadsheet

---

## Network Scanning

### IPv4 Scanning

The app uses nmap for IPv4 host discovery:
- **Network scan button** on each network card uses `nmap -sn <CIDR>`
- **Ping Scan page** uses ICMP ping with parallel threads
- **Nmap Scanner page** supports all scan types (SYN, service, OS detection)
- Discovered hosts are automatically added to the database

### IPv6 Scanning

For IPv6 networks, use the **Nmap Scanner** (Custom Command tab):
```
-6 -sn 2001:db8::/64
```

Note: Full IPv6 subnet sweeps are impractical due to address space size. Target specific known addresses or use neighbor discovery.

---

## Data Model

Both IPv4 and IPv6 addresses are stored in the same `ip_addresses` table:
- `address` field: stores any valid IP string (v4 or v6)
- `network_id`: links to a network (which can be IPv4 or IPv6 CIDR)
- All features (tags, notes, custom fields, devices) work identically regardless of protocol

The `networks` table supports both:
- `cidr` field: any valid CIDR notation (e.g., `192.168.1.0/24` or `2001:db8::/48`)
- Utilization calculation uses Python's `ipaddress` module which handles both protocols
