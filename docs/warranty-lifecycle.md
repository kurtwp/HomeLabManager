# Warranty & Lifecycle Tracking

Track purchase dates, warranty expiration, and end-of-life dates for your devices. Get dashboard warnings when warranties are about to expire.

## How It Works

Each device now has three optional date fields:

| Field | Purpose |
|-------|---------|
| Purchase Date | When the device was bought |
| Warranty Expiry | When the manufacturer warranty ends |
| End of Life Date | When the vendor stops supporting the product |

## Setting Warranty Info

1. Navigate to any device detail page (`/devices/{id}`)
2. Find the **Warranty & Lifecycle** card (below Physical Location)
3. Enter dates in `YYYY-MM-DD` format
4. Click **Save Warranty**

A status indicator shows:
- ✓ Green — warranty valid with days remaining
- ⚡ Orange — warranty expires within 30 days
- ⚠️ Red — warranty already expired

## Dashboard Widget

The main dashboard shows a warning card when devices have expiring or expired warranties (within 30 days):

- Orange left-border card with count of affected devices
- Lists device names with days until/since expiry
- Shows up to 5 devices, with "...and N more" for larger lists

The widget only appears when there are devices with warranty dates approaching or past expiration.

## Tips

- Set warranty dates when you first add devices — easier than tracking down receipts later
- Use End of Life date for hardware that's been EOL'd by the vendor (e.g. old UniFi models)
- The 30-day warning window gives you time to plan replacements or renewals
- Pair with custom fields for additional lifecycle data (vendor contact, support contract number)
