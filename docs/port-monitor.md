# Port Monitor

The **Port Monitor** checks that specific TCP services are responding on your network devices. Unlike Uptime Monitor (which pings hosts), Port Monitor verifies that individual services like HTTP, SSH, DNS, or databases are actually accepting connections.

## Accessing Port Monitor

Click **Monitor** in the top navigation → **Port Monitor**, or navigate to `/port-monitor`.

## How It Works

The port monitor attempts a TCP connection to the specified IP and port. If the connection succeeds within the timeout period, the service is considered "up" and the connection time is recorded as latency. If the connection is refused or times out, the service is "down."

## Adding a Port Monitor

Click **Add Port Monitor** and fill in:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly name (e.g. "Web Server HTTPS") |
| IP Address | Yes | Target host IP |
| TCP Port | Yes | Port number to check |
| Check Interval | Yes | How often to check (30s–5min) |
| Retries | Yes | Failed checks before marking down |
| Retry Interval | Yes | Time between retries |

### Common Port Shortcuts

Quick-select buttons for frequently monitored ports:

| Button | Port | Service |
|--------|------|---------|
| HTTP | 80 | Web server |
| HTTPS | 443 | Secure web |
| SSH | 22 | Secure shell |
| DNS | 53 | Domain name service |
| RDP | 3389 | Remote desktop |
| Alt HTTP | 8080 | Alternative web server |
| FTP | 21 | File transfer |
| SMTP | 25 | Email sending |
| MySQL | 3306 | MySQL database |
| Postgres | 5432 | PostgreSQL database |
| Redis | 6379 | Redis cache |
| UniFi | 8443 | UniFi controller |

## Multiple Ports Per IP

You can add multiple port monitors for the same IP address. For example:
- `192.168.2.10:80` — HTTP
- `192.168.2.10:443` — HTTPS
- `192.168.2.10:22` — SSH

Each monitor runs independently with its own status, check interval, and history.

## Dashboard Widget

The dashboard shows a **Port Monitor** card (teal icon) alongside the Uptime Monitor card. It displays:
- Number of services up (green) and down (red)
- Total services monitored
- Click to navigate to the Port Monitor page

## Detail Page

Clicking any port monitor navigates to `/uptime/{id}` — the same detail page used by uptime monitors, but labeled as "TCP Port :443" with a chart showing "TCP Connect Time (ms)" instead of ping latency.

Features on the detail page:
- Heartbeat bar (green/red blocks)
- Stats: current connect time, avg (24h), uptime (24h), uptime (30d)
- Response time chart with downtime highlighted
- Recent events

## Difference from Uptime Monitor

| | Uptime Monitor | Port Monitor |
|---|---|---|
| **What it checks** | Host reachability (ICMP ping) | Service availability (TCP port) |
| **Measures** | Ping latency (ms) | TCP connect time (ms) |
| **Use case** | Is the device on the network? | Is the service running? |
| **Page** | `/uptime` | `/port-monitor` |
| **Dashboard icon** | Purple (monitor_heart) | Teal (lan) |

A host can be up (responds to ping) while a service on it is down (port closed). That's why you'd monitor both.

## Tips

- Monitor critical services: web servers, databases, DNS, email
- A port check failing while ping succeeds means the service crashed but the host is still up
- Use shorter intervals (30s) for production services, longer (5min) for non-critical
- Same IP can have ping + multiple port monitors running independently
- Pair with notifications to get alerted when services go down
