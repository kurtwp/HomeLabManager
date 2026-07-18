# SSL Certificate Tracker

The **SSL Certificate Tracker** monitors TLS/SSL certificates on your internal services and alerts you before they expire.

## Accessing the SSL Tracker

Click **Monitor** in the top navigation → **SSL Certificates**, or navigate to `/ssl-tracker`.

## How It Works

1. You add services by name, host, and port (defaults to 443)
2. The tracker connects and retrieves the certificate details (issuer, subject, expiry)
3. Certificates are checked automatically every 12 hours
4. When a certificate enters the warning window (default 30 days), a notification is sent
5. Expired certs are flagged red on the page

## Adding a Certificate

Click **Add Certificate** and fill in:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly label (e.g. "Proxmox Web UI") |
| Host | Yes | IP or hostname of the service |
| Port | No | Port number (defaults to 443) |
| Alert when fewer than | No | Days before expiry to trigger alert (default 30) |

A **Test Connection** button lets you verify the cert is reachable before saving.

## Certificate Status

| Status | Meaning |
|--------|---------|
| ✅ Valid (green) | More than 30 days remaining |
| ⚠️ Expiring (orange) | 30 days or fewer remaining |
| ❌ Expired (red) | Certificate has expired |
| ❓ Not checked (gray) | Not yet scanned |
| 🔴 Error (red) | Connection failed or cert unreadable |

## Summary Badges

The top of the page shows counts: Valid, Expiring Soon, Expired, Not Checked.

## Self-Signed Certificates

The tracker works with self-signed certificates (common on home lab devices like UniFi, Proxmox, Synology). It doesn't validate the trust chain — it only checks the expiry date.

## Notifications

Alerts are sent through all enabled notification channels when a certificate enters the warning zone:

- **Normal priority** — when days remaining ≤ alert threshold (default 30)
- **High priority** — when 7 days or fewer remain

Notifications fire once when the cert first enters the warning zone (not repeated daily).

## Automatic Checking

A background job runs every 12 hours to check all tracked certificates. You can also:
- Click **Check All** to scan everything immediately
- Click the refresh icon on individual certs for a single check

## What's Tracked

| Field | Description |
|-------|-------------|
| Subject | Certificate CN or subject name |
| Issuer | Who issued the cert (Let's Encrypt, self-signed, etc.) |
| Not Before | When the cert became valid |
| Not After | Expiry date |
| Days Remaining | Calculated from current date |
| Last Checked | When the last scan ran |

## Common Services to Track

| Service | Default Port | Example Host |
|---------|:---:|---|
| UniFi Controller | 443 | 192.168.2.254 |
| Proxmox VE | 8006 | 192.168.2.10 |
| Synology DSM | 5001 | 192.168.2.20 |
| Home Assistant | 8123 | 192.168.2.30 |
| Portainer | 9443 | 192.168.2.40 |
| Any HTTPS service | 443 | — |

## Requirements

- `openssl` must be installed on the server (usually pre-installed on Ubuntu)
- The service must be reachable from the server running Home Lab Manager
- The service must present a TLS certificate (any cert, including self-signed)

## Tips

- Track all internal HTTPS services — especially self-signed certs that you generate manually
- Set alert_days to 60 for Let's Encrypt certs (they're 90-day certs, auto-renewed at 30 days)
- Set alert_days to 30 for self-signed certs you manage manually
- Use the Test button before saving to verify connectivity
- Pair with notifications to get emailed/messaged before certs expire
