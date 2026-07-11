# Discovery Features

The Discovery dropdown menu provides all network scanning and device discovery tools available in the Home Lab IP Manager.

---

## Menu Items

| Tool | Route | Description |
|------|-------|-------------|
| UniFi Sync (Local) | `/unifi` | Pull data from your local UniFi controller |
| Site Manager (Cloud) | `/site-manager` | Cloud API for cross-site UniFi overview |
| SNMP Discovery | `/snmp` | Query devices for system info via SNMP |
| Nmap Scanner | `/nmap` | Run nmap commands with GUI interface |
| Ping Scan | `/ping-scan` | Fast ICMP host discovery using fping/ping |
| Uptime Monitor | `/uptime` | Continuous monitoring of critical hosts |
| Scheduled Scans | `/scheduler` | Configure recurring automatic scans |

---

## UniFi Sync (Local)

**Purpose:** Pull networks, devices, and clients directly from your local UniFi controller.

**Requirements:**
- UniFi API key (generated at Console → Integrations)
- Console IP reachable from the server
- Set `UNIFI_API_KEY`, `UNIFI_BASE_URL`, `UNIFI_SITE_ID` in `.env`

**Capabilities:**
- **Test Connection** — verify API key and connectivity
- **Sync Networks** — pulls VLANs/subnets with gateway and DHCP range
- **Sync Devices** — pulls APs, switches, gateways with IPs and device types
- **Sync Clients** — pulls all connected clients with hostnames and MACs
- **Sync Everything** — one-click full sync

**Behavior:**
- Automatically classifies IPs as Static or DHCP based on DHCP ranges
- Marks disconnected clients as inactive after each sync
- Detects duplicates by MAC address and hostname
- Tags IPs with source (`unifi_client`, `unifi_device`)
- Infrastructure devices get their management IPs linked

**Debug:** Expandable "Raw API Data" section shows actual JSON responses from the controller.

---

## Site Manager (Cloud)

**Purpose:** Cross-site overview of all UniFi deployments via Ubiquiti's cloud API.

**Requirements:**
- Cloud API key from unifi.ui.com → Settings → API Keys
- Set `UNIFI_CLOUD_API_KEY` in `.env`

**Tabs:**
- **Hosts** — list all controllers (UDM SE, UCK, etc.) with firmware info
- **Sites** — all sites across all hosts with device counts
- **Devices** — all devices across all sites (current + previous locations)
- **ISP Metrics** — latency, bandwidth, uptime, packet loss per site/WAN

**ISP Metrics Details:**
- Endpoint: `GET /v1/isp-metrics/5m` (5-minute intervals) or `/v1/isp-metrics/1h` (hourly)
- Shows per-site: ISP name, avg latency, download/upload speed, uptime %, packet loss
- Supports multiple WANs (wan, wan2) if configured
- Expandable history table with all data points
- Requires: UniFi OS 5.0.3+, Network App 8.3.32+

---

## SNMP Discovery

**Purpose:** Query network devices for detailed system information via SNMP protocol.

**Requirements:**
- `snmpget` and `snmpwalk` installed (`sudo apt install snmp`)
- Target devices must have SNMP enabled with correct community string

**SNMP Versions Supported:**
- **SNMPv1** — community string only
- **SNMPv2c** (default) — community string only
- **SNMPv3** — username, security level, auth/priv protocols and passwords

**Tabs:**
- **Query Single Device** — enter an IP, get full system info
- **Scan Network** — probe all known IPs in a network for SNMP-enabled devices
- **Query Known Devices** — SNMP query all IPs in the database

**Information Gathered:**
- System name, description, location, contact
- Uptime
- Object ID
- Interface count with details (name, status up/down, speed, MAC)

**Save:** Click "Save to Database" to store results as a Note on the IP.

---

## Nmap Scanner

**Purpose:** Run nmap scans with a full GUI — port scanning, OS detection, service version identification.

**Requirements:**
- `nmap` installed (`sudo apt install nmap`)
- For privileged scans: `echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/nmap" | sudo tee /etc/sudoers.d/nmap`

**Tabs:**
- **Quick Scan** — pick target + scan type from presets
- **Custom Command** — enter any nmap arguments freeform

**Quick Scan Presets:**
| Scan Type | Command | Requires Sudo |
|-----------|---------|:-------------:|
| Ping Scan | `-sn` | No |
| SYN Scan | `-sS` | Yes |
| TCP Connect | `-sT` | No |
| Service Version | `-sV` | No |
| Service + OS | `-sV -O` | Yes |
| Aggressive | `-A` | Yes |
| Common Ports | `-p 1-1024` | No |
| All Ports | `-p-` | Recommended |

**Features:**
- "Run as root (sudo)" toggle for privileged scans
- Timing options (T2–T5)
- Extra arguments field
- Results parsed into expandable host cards with port tables
- Raw output always available
- "Save Results to Database" — saves OS/port info as Notes on each IP
- Clear button to reset inputs
- Background thread execution (no "Connection lost" on long scans)
- 30-minute timeout for large scans

---

## Ping Scan

**Purpose:** Fast ICMP host discovery — find what's alive on a network.

**Requirements:**
- `fping` recommended (`sudo apt install fping`) — ~1 second for a /24
- Falls back to threaded `ping` if fping not installed (~5 seconds for a /24)

**Features:**
- Select target by typing CIDR or picking from known networks
- Configurable timeout (1–5 seconds)
- Results show IP, hostname (reverse DNS), and latency
- Automatically saves discovered IPs to the database
- Classifies as Static or DHCP using DHCP range settings
- Shows scan method badge (`fping` or `ping`)
- Summary badges: alive count, no-response count, new IPs added, updated

**How it Saves:**
- New IPs are created with source `ping_scan`
- Existing IPs get `last_seen` and `status` updated
- IPs not matching any network in the DB are skipped

---

## Uptime Monitor

**Purpose:** Continuously monitor critical hosts — get alerted when they go down.

**How it works:**
- Background scheduler pings all monitored hosts every 30 seconds
- Each host has its own configurable check interval (20s–10m)
- Configurable retries and retry interval before marking a host as down
- Tracks status transitions (up → down, down → up/recovered)
- Logs events with timestamps
- Records every ping result (latency + status) for historical graphing

**Monitoring Profiles (Presets):**

| Profile | Heartbeat Interval | Retries | Retry Interval | Time to Alert |
|---------|-------------------|---------|----------------|---------------|
| Standard / Internal Devices | 60 seconds | 3 | 30 seconds | ~90 seconds |
| Critical Infrastructure | 30 seconds | 2 | 10 seconds | ~20 seconds |
| Non-Critical / IoT Devices | 300 seconds (5 min) | 3 | 60 seconds | ~3 minutes |
| Custom | User-defined | User-defined | User-defined | Varies |

**Features:**
- Add hosts with preset profiles or fully custom timing values
- Edit monitors (name, IP, interval, retries, retry interval, enable/disable)
- Dashboard widget shows up/down counts (clickable → uptime page)
- Summary badges: X Up, X Down — clickable to filter the list
- Quick check button — instant ping test per host
- Event history per host (collapsible) — shows when hosts went down/recovered
- Remove monitoring with confirmation
- Notifications — automatic alerts when hosts go down or recover (only after retries exhausted)

**Detail Page** (click any host card → `/uptime/{id}`):
- **Heartbeat bar** — visual row of colored blocks showing recent check results (green = up, red = down)
- **Stats row:**
  - Ping (Current) — latest latency in ms
  - Avg. Ping (24-hour) — average latency over 24 hours
  - Uptime (24-hour) — percentage over last 24 hours
  - Uptime (30-day) — percentage over last 30 days
- **Response time chart** — ECharts line graph of latency over time:
  - Selectable time range: 1h, 3h, 6h, 12h, 24h
  - Green line with shaded area
  - Red shaded zones marking downtime periods
  - Dashed average latency reference line
- **Recent events** — status changes with timestamps and details

**Metrics Tracked:**
- Current status (up/down/unknown)
- Uptime percentage (total_up / total_checks × 100)
- Consecutive failures
- Max retries and retry interval per host
- Last seen up / last seen down timestamps
- Total check count
- Per-check latency history (stored in ping_results table)

---

## Scheduled Scans

**Purpose:** Configure recurring automatic network scans on a schedule.

**Features:**
- Schedule ping scans per-network
- Configurable intervals: 15min, 30min, 1h, 2h, 6h, 12h, 24h
- View active schedules with next run time
- Remove scheduled jobs
- Uses APScheduler background scheduler

**How it works:**
- Scheduled jobs run `nmap -sn` on the configured network CIDR
- Discovered hosts are added to the database automatically
- Missing hosts are marked inactive (respecting DHCP range and recent-seen protection)

---

## MAC OUI Fingerprinting

**Where:** Shown on the IP detail page in the Details card.

**What it does:** Resolves the first 3 bytes of a MAC address to the manufacturer/vendor name using the IEEE OUI database.

**Examples:**
- `60:22:32:89:B4:34` → Ubiquiti Inc
- `F4:39:09:49:57:57` → Hewlett Packard
- `3C:8D:20:E4:CD:2D` → Google Inc

**Database:** `mac-vendors.txt` in the project root (39,719 entries). Loaded into memory at startup.

---

## Comparison of Scan Methods

| Method | Speed (/24) | Finds | Root Needed | Adds to DB |
|--------|-------------|-------|:-----------:|:----------:|
| fping | ~1 sec | Alive hosts | No | Yes |
| Threaded ping | ~5 sec | Alive hosts | No | Yes |
| nmap -sn | ~5 sec | Alive hosts (ARP on local) | No | Yes (via network scan button) |
| nmap -sV | 5-30 min | Ports + services | No (sudo better) | Yes (Save button) |
| nmap -A | 15-30 min | OS + ports + services | Yes | Yes (Save button) |
| SNMP | ~2 sec/host | System info, interfaces | No | Yes (Save button) |
| UniFi Sync | ~3 sec | Clients, devices, networks | No | Yes (auto) |

---

## Recommended Workflow

1. **First time setup:** Sync from UniFi (if available) or manually add a network
2. **Initial discovery:** Run a Ping Scan or use the Network scan button
3. **Detailed info:** Run nmap Service + OS detection on specific IPs of interest
4. **SNMP:** Query managed switches/servers that have SNMP enabled
5. **Ongoing:** Set up scheduled scans + uptime monitoring for critical hosts
6. **Classify:** Click IPs to set device types for newly discovered hosts
