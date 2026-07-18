# Webhook Triggers

Webhook Triggers let you fire HTTP POST requests to external services when specific events occur in Home Lab Manager. Use them to integrate with Slack, Discord, Home Assistant, n8n, or any HTTP endpoint.

## Accessing Webhook Triggers

Click the **wrench icon** (🔧) → **Webhook Triggers**, or navigate to `/webhook-triggers`.

## Difference from Notifications

| | Notifications | Webhook Triggers |
|---|---|---|
| Purpose | Alert you about problems | Automate workflows |
| Channels | Email, Pushover, one webhook URL | Per-trigger custom URLs |
| Events | Fixed (monitor down/up, firmware) | Configurable (9 event types) |
| Config | .env file / Settings page | UI-based rules |
| Filter | None | Optional per-trigger filter |

Both can coexist — notifications alert you, triggers automate responses.

## Available Events

| Event | Fires When | Status |
|-------|-----------|--------|
| `monitor_down` | An uptime or port monitor goes down | ✅ Active |
| `monitor_up` | A monitor recovers | ✅ Active |
| `scan_complete` | A network scan (ping/nmap) finishes | ✅ Active |
| `ip_active` | A new IP is discovered during a scan | ✅ Active |
| `ip_inactive` | An IP is marked inactive during a scan | ✅ Active |
| `unknown_mac` | Unrecognized MACs found after a scan | ✅ Active |
| `firmware_update` | A firmware update is available for a device | ✅ Active |
| `new_device` | A new device is added to the inventory | 🔜 Planned |
| `capacity_warning` | A network's utilization exceeds 80% | 🔜 Planned |

## Creating a Trigger

Click **Add Trigger** and configure:

| Field | Required | Description |
|-------|----------|-------------|
| Name | Yes | Friendly label (e.g. "Slack on monitor down") |
| Event | Yes | Which event type fires this trigger |
| Webhook URL | Yes | The HTTP endpoint to POST to |
| Filter | No | Narrow which events match (see below) |

## Filters

Filters are optional strings that narrow when a trigger fires. The filter is matched against any value in the event payload.

Examples:
- Filter: `192.168.2` → only fires for events involving IPs in that subnet
- Filter: `Main Server` → only fires for events mentioning "Main Server"
- Filter: `critical` → fires for anything containing "critical"
- Empty filter → fires on ALL matching events

## Webhook Payload

Each webhook receives a JSON POST body like:

```json
{
  "event": "monitor_down",
  "trigger_name": "Slack alert on down",
  "timestamp": "2026-07-18T10:30:00+00:00",
  "source": "Home Lab Manager",
  "name": "Web Server",
  "ip_address": "192.168.2.10",
  "monitor_type": "port",
  "port": 443,
  "consecutive_failures": 3
}
```

The payload includes the event type, trigger name, timestamp, and event-specific data.

## Managing Triggers

Each trigger card shows:
- Name and event type badge
- Filter (if set)
- Enabled/disabled status
- Fire count and last fired timestamp
- Webhook URL (truncated)

Actions:
- **Test** (send icon) — sends a test payload to verify the URL works
- **Edit** — modify any field, enable/disable
- **Delete** — remove the trigger

## Integration Examples

### Slack
```
URL: https://hooks.slack.com/services/T00/B00/xxxx
```
Slack incoming webhooks accept JSON with a `text` field. You may need a middleware (n8n, Zapier) to reformat the payload, or use Slack's workflow builder.

### Discord
```
URL: https://discord.com/api/webhooks/xxxx/yyyy
```
Discord webhooks expect `{"content": "message"}`. Use a middleware to transform the payload.

### Home Assistant
```
URL: http://homeassistant.local:8123/api/webhook/my-trigger-id
```
Create an automation in HA triggered by a webhook, then use the payload data in your automation.

### n8n / Node-RED
Point the URL at your n8n webhook node or Node-RED HTTP-in node. The full JSON payload is available for processing.

## Tips

- Use the **Test** button after creating a trigger to verify it works
- Filters are case-insensitive and match any payload value
- Disabled triggers don't fire but keep their configuration
- Fire count helps you understand how active a trigger is
- Multiple triggers can fire on the same event (e.g. one to Slack, one to Home Assistant)
- The same IP can be mentioned in multiple event types (down, up, inactive, etc.)
