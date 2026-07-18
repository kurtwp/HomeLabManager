# Notifications

The **Notifications** feature sends alerts through multiple channels when important events occur — like a monitored host going down or a firmware update becoming available.

## Accessing Notifications Settings

Click the **wrench icon** (🔧) in the top-right → **Notifications**, or navigate to `/notifications`.

## Supported Channels

| Channel | How It Works |
|---------|-------------|
| Email (SMTP) | Sends email via any SMTP server (Gmail, Office 365, self-hosted) |
| Webhook | Sends a JSON POST to any URL (Slack, Discord, Teams, custom endpoints) |
| Pushover | Sends push notifications to iOS/Android via the Pushover app |
| Telegram | Sends messages to a Telegram chat or group via Bot API |

Multiple channels can be enabled simultaneously — alerts are sent to all active channels.

## Configuration

All notification settings are configured via environment variables in your `.env` file.

### Global Toggle

```bash
NOTIFICATIONS_ENABLED=true
```

This must be `true` for any notifications to fire. Individual channels can then be enabled/disabled independently.

### Email (SMTP)

```bash
NOTIFY_EMAIL_ENABLED=true
NOTIFY_SMTP_HOST=smtp.gmail.com
NOTIFY_SMTP_PORT=587
NOTIFY_SMTP_USER=you@gmail.com
NOTIFY_SMTP_PASS=your_app_password
NOTIFY_SMTP_FROM=homelab@yourdomain.com
NOTIFY_SMTP_TO=admin@yourdomain.com
NOTIFY_SMTP_TLS=true
```

- For Gmail, use an [App Password](https://myaccount.google.com/apppasswords) rather than your main password
- `NOTIFY_SMTP_TO` supports multiple recipients (comma-separated)
- Set `NOTIFY_SMTP_TLS=false` for SMTP servers that don't use STARTTLS

### Webhook

```bash
NOTIFY_WEBHOOK_ENABLED=true
NOTIFY_WEBHOOK_URL=https://hooks.slack.com/services/T00/B00/xxxx
```

The webhook sends a JSON POST with this structure:

```json
{
  "subject": "🔴 Host DOWN: My Server (192.168.1.5)",
  "message": "Host 'My Server' at 192.168.1.5 is not responding...",
  "priority": "high",
  "timestamp": "2026-07-10T12:00:00+00:00",
  "source": "HomeLab Manager"
}
```

Works with Slack incoming webhooks, Discord webhooks (with a formatting adapter), n8n, Home Assistant, or any custom HTTP endpoint.

### Pushover

```bash
NOTIFY_PUSHOVER_ENABLED=true
NOTIFY_PUSHOVER_TOKEN=your_app_token
NOTIFY_PUSHOVER_USER=your_user_key
```

- Create an application at [pushover.net](https://pushover.net) to get your token
- Priority levels map to Pushover's native priorities (critical triggers emergency alerts with repeat)

### Telegram

```bash
NOTIFY_TELEGRAM_ENABLED=true
NOTIFY_TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
NOTIFY_TELEGRAM_CHAT_ID=your_chat_id
```

**Setup steps:**
1. Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → follow prompts → get your bot token
2. Start a conversation with your new bot (send it any message)
3. Get your chat ID: visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser → find `"chat":{"id":123456789}` in the response
4. Add the token and chat ID to your `.env` or Settings page

**For group chats:** Add the bot to the group, send a message in the group, then check `getUpdates` for the group's chat ID (negative number like `-1001234567890`).

## Alert Triggers

The following events automatically send notifications:

| Event | Priority | When |
|-------|----------|------|
| 🔴 Host Down | High | An uptime-monitored host stops responding |
| 🟢 Host Recovered | Normal | A previously-down host comes back online |
| 📦 Firmware Update | Low | A new firmware version is detected for a UniFi device |

## Testing Notifications

On the Notifications page, use the **Send Test** button to verify your configuration. It sends a test message through all enabled channels and reports which succeeded or failed.

## Notification History

The bottom of the Notifications page shows a history log of all sent notifications:

- Timestamp
- Channel used (email, webhook, pushover)
- Subject/message
- Success or failure (with error details)

This helps troubleshoot delivery issues without checking external services.

## How It Works

1. The **uptime monitor** runs every 30 seconds and checks all enabled hosts
2. When a host transitions from up → down (or down → up), the notification service is called
3. The **firmware checker** runs every 6 hours and compares device firmware versions
4. When a new update is first detected, a notification fires
5. All notifications are logged to the database regardless of delivery success

## Tips

- Start with just one channel to verify it works, then add more
- The webhook channel is the most flexible — it can integrate with almost anything
- Pushover is ideal for mobile push notifications with sound alerts
- Use Gmail app passwords or a dedicated SMTP relay for email reliability
- Check the notification history if alerts aren't arriving — errors are logged there
- Restart the application after changing `.env` notification settings
