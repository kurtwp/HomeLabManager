# Domain Tracker

The **Domain Tracker** monitors domain registration expiry dates and alerts you before domains lapse.

## Accessing the Domain Tracker

Click **Monitor** in the top navigation → **Domain Tracker**, or navigate to `/domain-tracker`.

## How It Works

1. You add domains you own (e.g. `example.com`)
2. The tracker performs a WHOIS lookup to get registration details and expiry date
3. Domains are checked automatically every 24 hours
4. When a domain enters the warning window, a notification is sent

## Adding a Domain

Click **Add Domain** and fill in:

| Field | Required | Description |
|-------|----------|-------------|
| Domain | Yes | The domain name (e.g. `mysite.com`) |
| Alert when fewer than | No | Days before expiry to alert (default 30) |
| Auto-Renew enabled | No | Mark if auto-renew is on at your registrar |
| Notes | No | Registrar account info, contact, etc. |

A **Test WHOIS Lookup** button lets you verify the domain is resolvable before saving.

## Domain Status

| Status | Meaning |
|--------|---------|
| ✅ Valid (green) | More than 30 days remaining |
| ⚠️ Expiring (orange) | 30 days or fewer remaining |
| ❌ Expired (red) | Domain has expired |
| ❓ Not checked (gray) | Not yet looked up |
| 🔴 Error (red) | WHOIS lookup failed |

## Information Retrieved

| Field | Description |
|-------|-------------|
| Registrar | Who the domain is registered through |
| Creation Date | When the domain was first registered |
| Expiry Date | When the registration expires |
| Days Remaining | Calculated from current date |
| Name Servers | DNS servers for the domain |
| Auto-Renew | Whether you've marked it as auto-renewing |

## Notifications

Alerts fire when a domain enters the warning window:

- **Normal priority** — when days remaining ≤ alert threshold
- **High priority** — when 7 days or fewer remain

The auto-renew flag is informational only — the system doesn't check if renewal actually happened. It's there so you know which domains need manual attention.

## Automatic Checking

A background job runs every 24 hours to WHOIS-check all tracked domains. You can also:
- Click **Check All** for immediate scan of everything
- Click the refresh icon per domain for individual checks

## Requirements

- `whois` must be installed: `sudo apt install whois`
- The server must have internet access (WHOIS queries go to registry servers)
- Some registrars rate-limit WHOIS queries — if you get errors, wait and retry

## Tips

- Track all domains you own, even if they auto-renew — registrar billing issues can cause lapses
- Set longer alert windows (60-90 days) for critical business domains
- Use the Notes field to record which registrar account owns each domain
- The auto-renew toggle helps you focus attention on domains that need manual renewal
- WHOIS data may be up to 24h stale depending on the registry
