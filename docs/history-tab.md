# History Tab

The **History** tab provides a complete audit trail of every change made to your home lab inventory. Every time a network, IP, device, tag, or documentation article is created, updated, or deleted, it's logged here with full before/after details.

## Accessing the History Tab

Click **History** in the top navigation bar, or navigate to `/history`.

## Changelog View

The main view lists changelog entries in reverse chronological order (newest first), showing up to 200 entries. Each entry displays:

- **Action icon** — color-coded by action type:
  - 🟢 Green circle: Created
  - 🔵 Blue pencil: Updated
  - 🔴 Red circle: Deleted
- **Action label** — e.g. "Created Network", "Updated IP Address", "Deleted Device"
- **Entity name** — the specific item affected (e.g. "Main LAN", "192.168.1.50")
- **Timestamp** — when the change occurred
- **Comment** — optional note (if one was attached)
- **Diff** — for updates, shows what changed in `field: old → new` format

### Diff Display

When an entity is updated, the changelog stores both old and new values as JSON. The History page renders this as a compact diff:

```
hostname: — → my-server | status: unknown → active
```

This makes it easy to see exactly what changed without digging into individual records.

## Filtering

Two filter dropdowns are available and auto-refresh the list when changed:

| Filter | Options |
|--------|---------|
| Entity Type | All, Network, IP Address, Device, Documentation, Tag |
| Action | All, Created, Updated, Deleted |

Combine both filters to narrow results (e.g. show only deleted devices, or only network updates).

## Retention Management

The History tab includes built-in retention controls to prevent the changelog from growing indefinitely:

### Purge by Age

Select a retention period and click **Purge Now** to delete entries older than:
- 30 days
- 60 days
- 90 days
- 6 months
- 1 year

### Clear All

The **Clear All** button removes every changelog entry. A confirmation dialog shows the total count and warns that this cannot be undone.

## What Gets Logged

The system automatically logs changes for these entity types:

| Entity Type | Logged Actions |
|-------------|---------------|
| Network | Create, update (name, CIDR, VLAN, DHCP range, etc.), delete |
| IP Address | Create, update (hostname, status, assignment type, etc.), delete |
| Device | Create, update (name, type, location, etc.), delete |
| Documentation | Create, update, delete |
| Tag | Create, update, delete |

### What's Stored Per Entry

| Field | Description |
|-------|-------------|
| Entity Type | Which type of item was changed |
| Entity ID | Internal ID of the item |
| Entity Name | Human-readable name (IP address, device name, etc.) |
| Action | Created, Updated, or Deleted |
| Old Values | JSON of previous values (for updates and deletes) |
| New Values | JSON of new values (for creates and updates) |
| Comment | Optional annotation |
| Timestamp | UTC time of the change |

## Important Notes

- **Changelog survives deletion** — when you delete an IP or device, the history entries for that item remain. This is intentional for audit purposes.
- **Bulk deletes** — using "Delete All" on the IPs or Devices page removes the items but preserves their changelog history.
- **No undo** — the changelog is read-only. It records what happened but cannot revert changes.
- **Automatic logging** — changes are logged by the service layer. No manual action is needed to create history entries.

## Tips

- Check History after running a sync or scan to see what was added/changed
- Use the Entity Type filter to review all changes to a specific type (e.g. all network modifications)
- Set up a retention policy to keep the changelog from growing too large over time
- The "Deleted" filter is useful for finding items that were accidentally removed
- Before/after diffs make it easy to audit configuration changes
