# Backup & Restore

The **Backup & Restore** feature provides one-click database backups and the ability to restore from any previous backup — all from the UI.

## Accessing Backup & Restore

Click the **wrench icon** (🔧) → **Backup & Restore**, or navigate to `/backup`.

## Creating a Backup

1. Click **Create Backup Now**
2. The current database is copied to the `backups/` directory with a timestamped filename
3. A confirmation shows the filename and size

Backups are named: `backup_YYYYMMDD_HHMMSS.db`

## What's Included

A backup contains the complete SQLite database — everything:
- Networks, VLANs, and utilization data
- IP addresses with all metadata
- Devices with types, locations, and custom fields
- Tags and tag assignments
- Documentation/knowledge base articles
- Change history (changelog)
- Uptime monitoring data and ping history
- Notification logs
- Firmware tracking data
- PSTN/telephony data (if using the separate PSTN database, that is NOT included — back it up separately)

## Restoring a Backup

1. Find the backup you want to restore in the list
2. Click the **restore** (orange) button
3. Confirm the restore in the dialog
4. **Restart the application** — the restored data takes effect on next startup

Before restoring, the system automatically creates a safety backup of the current database named `pre_restore_YYYYMMDD_HHMMSS.db` so you can always go back.

## Managing Backups

- **List** — all backups are shown with filename, size, and creation date
- **Delete** — remove old backups you no longer need (with confirmation)
- Backups are stored in the `backups/` directory alongside your application

## Storage

Backups are plain SQLite `.db` files. Each backup is roughly the same size as your current database (shown at the top of the page). For a typical home lab with a few hundred IPs and devices, this is usually under 10 MB.

## When to Back Up

- Before bulk imports or "Delete All" operations
- Before application upgrades
- Before restoring a different backup
- After completing a major configuration effort you don't want to repeat
- On a regular schedule (weekly/monthly) for peace of mind

## Tips

- The `backups/` directory is gitignored — backups stay local to your server
- You can manually copy backup files off the server for offsite storage
- Backup files are standard SQLite — you can open them with any SQLite tool for inspection
- The safety backup on restore means you can always undo a restore by restoring the `pre_restore_*` file
- For automated backups, you could set up a cron job that copies the `.db` file to a backup location
