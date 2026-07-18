# Monitoring

The **Monitor** menu provides continuous monitoring of your infrastructure — checking host availability, service ports, and firmware versions. All monitors share the same underlying engine with configurable intervals, retries, notifications, and historical graphing.

Access via the **Monitor** dropdown in the top navigation bar.

## Menu Items

| Item | Route | Purpose |
|------|-------|---------|
| Uptime Monitor | `/uptime` | Ping (ICMP) monitoring of host reachability |
| Port Monitor | `/port-monitor` | TCP port monitoring of service availability |
| Firmware Tracker | `/firmware` | Track UniFi device firmware versions |

---

## Uptime Monitor

**Purpose:** Continuously ping hosts to verify they're reachable on the network.

**Access:** Monitor → Uptime Monitor, or `/uptime`

### Adding a Monitor

Click **Add Host** and configure:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly label (e.g. "Main Server") |
| IP Address | Yes | Target host to ping |
| Profile | Yes | Preset timing or Custom |

### Monitoring Profiles

| Profile | Heartbeat Interval | Retries | Retry Interval | Time to Alert |
|---------|-------------------|---------|----------------|---------------|
| Standard / Internal Devices | 60 seconds | 3 | 30 seconds | ~90 seconds |
| Critical Infrastructure | 30 seconds | 2 | 10 seconds | ~20 seconds |
| Non-Critical / IoT Devices | 300 seconds (5 min) | 3 | 60 seconds | ~3 minutes |
| Custom | User-defined | User-defined | User-defined | Varies |

### How It Works

1. The scheduler pings each enabled host at its configured interval
2. If a ping fails, it enters retry mode (faster checks at the retry interval)
3. Only after all retries are exhausted is the host marked "down"
4. Notifications fire on status transitions (up → down, down → recovered)
5. **Reminder notifications** are sent every 24 hours while a host remains down
6. Every check records latency for historical graphing

### Features

- Clickable status filter badges (Up / Down) on the list page
- Quick check button for instant manual ping
- Edit monitors: name, IP, interval, retries, enable/disable
- Dashboard widget shows up/down counts

### Detail Page

Click any host card to see `/uptime/{id}`:

- **Heartbeat bar** — colored blocks showing recent check results
- **Stats row:** Current ping, Avg ping (24h), Uptime (24h), Uptime (30d)
- **Response time chart** — line graph with selectable range (1h–24h), downtime shown as red bands
- **Recent events** — status change history

---

## Port Monitor

**Purpose:** Check that specific TCP services are responding (HTTP, SSH, DNS, databases, etc.).

**Access:** Monitor → Port Monitor, or `/port-monitor`

### Adding a Port Monitor

Click **Add Port Monitor** and configure:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly label (e.g. "Web Server HTTPS") |
| IP Address | Yes | Target host |
| TCP Port | Yes | Port number to check |
| Check Interval | Yes | How often to check (30s–5min) |
| Retries | Yes | Failed checks before alerting |
| Retry Interval | Yes | Time between retries |

### Common Port Shortcuts

Quick-select buttons in the add dialog:

| Port | Service | Port | Service |
|------|---------|------|---------|
| 80 | HTTP | 3389 | RDP |
| 443 | HTTPS | 3306 | MySQL |
| 22 | SSH | 5432 | PostgreSQL |
| 53 | DNS | 6379 | Redis |
| 8080 | Alt HTTP | 8443 | UniFi |
| 21 | FTP | 25 | SMTP |

### Multiple Ports Per IP

The same IP can have multiple port monitors. Example:
- `192.168.2.10` — Ping (via Uptime Monitor)
- `192.168.2.10:80` — HTTP
- `192.168.2.10:443` — HTTPS
- `192.168.2.10:22` — SSH

Each runs independently with its own status and history.

### How It Works

1. Opens a TCP socket to the target IP:port
2. If connection succeeds, the service is "up" — connection time is recorded as latency
3. If connection is refused or times out, the service is "down"
4. Same retry logic as uptime monitoring before alerting

### Detail Page

Same as uptime monitors but labeled "TCP Port :443" with Y-axis showing "TCP Connect Time (ms)".

### Difference from Uptime Monitor

| | Uptime Monitor | Port Monitor |
|---|---|---|
| Checks | Host reachability (ICMP ping) | Service availability (TCP port) |
| Measures | Ping latency | TCP connect time |
| Use case | Is the device on? | Is the service running? |
| Dashboard icon | Purple (monitor_heart) | Teal (lan) |

A host can respond to ping while a service on it is down — that's why you'd monitor both.

---

## Firmware Tracker

**Purpose:** Monitor UniFi device firmware versions and get notified of available updates.

**Access:** Monitor → Firmware Tracker, or `/firmware`

### How It Works

1. Pulls device data from the UniFi Integration API
2. Extracts current firmware version and available upgrade version
3. Tracks each device by MAC address
4. When a new update is detected, sends a notification
5. Runs automatically every 6 hours via the scheduler

### Firmware Page

- **Summary cards:** Total tracked, up-to-date, updates available
- **Updates Available section:** Highlighted cards showing device name, current version, available version
- **Up to Date section:** Table of devices running latest firmware
- **Manual check button:** Run an immediate scan

### Data Tracked

| Field | Description |
|-------|-------------|
| Device MAC | Unique identifier |
| Device Name | From UniFi |
| Model | Hardware model |
| Current Version | Running firmware |
| Available Version | Upgrade available (if any) |
| Last Checked | When last scanned |
| Last Updated | When firmware version changed |

### Notifications

When a firmware update is newly detected, an alert is sent through all enabled notification channels (email, webhook, Pushover) with low priority.

### Requirements

- UniFi Integration must be configured (API key, base URL, site ID in `.env`)
- Devices must be managed by the UniFi controller

---

## Dashboard Integration

The main dashboard shows both monitor widgets side by side:

- **Uptime Monitor** (purple) — up/down count for ping monitors, clickable → `/uptime`
- **Port Monitor** (teal) — up/down count for port monitors, clickable → `/port-monitor`

---

## Notifications

All three monitor types integrate with the notification system:

| Event | Source | Priority |
|-------|--------|----------|
| Host down | Uptime Monitor | High |
| Host still down (24h reminder) | Uptime Monitor | High |
| Host recovered | Uptime Monitor | Normal |
| Service port down | Port Monitor | High |
| Service still down (24h reminder) | Port Monitor | High |
| Service recovered | Port Monitor | Normal |
| Firmware update available | Firmware Tracker | Low |

The 24-hour reminder repeats daily until the host/service recovers or the monitor is removed.

Configure notifications at Tools → Notifications or see the [Notifications](notifications) documentation.

---

## Tips

- Use Uptime Monitor for "is the device on the network?" checks
- Use Port Monitor for "is the service running?" checks  
- Monitor both ping + key ports on critical servers for complete coverage
- Shorter intervals (30s) for production services, longer (5min) for non-critical
- The detail page heartbeat bar gives instant visual status at a glance
- Check firmware weekly to stay on top of security patches
- Notifications ensure you know about issues even when not looking at the dashboard
