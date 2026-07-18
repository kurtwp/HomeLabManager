# MAC Watchlist

The **MAC Watchlist** provides network awareness by maintaining a list of known/approved MAC addresses and flagging when unrecognized devices appear on your network.

## Important Note

This feature is for **visibility only** — it does not block or prevent unknown devices from connecting. It alerts you that something new showed up so you can investigate. Actual network access control requires 802.1X, MAC ACLs on your switch, or UniFi's built-in client blocking.

## Accessing the MAC Watchlist

Click the **wrench icon** (🔧) → **MAC Watchlist**, or navigate to `/mac-watchlist`.

## How It Works

1. You build a list of known/approved MAC addresses (your devices)
2. After each UniFi sync or network scan, new MACs are discovered
3. Any MAC not on the known list is flagged as "unknown"
4. Unknown devices appear on the dashboard and the MAC Watchlist page

## Page Layout

### Unknown Devices (top)

A table of active MACs not in your known list:
- MAC address
- Manufacturer (via OUI lookup)
- IP address
- Hostname
- Network
- Source (UniFi, Nmap, etc.)
- **Approve** button — add to known list with one click

### Known MACs (bottom)

A table of all approved MAC addresses:
- MAC address
- Name (device label)
- Notes
- Date added
- **Delete** button — remove from known list

## Adding Known MACs

Three ways to populate your known list:

### 1. Approve All Current
Click **Approve All Current** to bulk-add every active MAC on your network to the known list. Good for initial setup — "everything on my network right now is legit."

### 2. Approve Individually
On the Unknown Devices table, click **Approve** next to any device you recognize. It's added with the hostname/IP as its name.

### 3. Add Manually
Click **Add MAC** and enter:
- MAC address (AA:BB:CC:DD:EE:FF)
- Name (friendly label)
- Notes (optional)

## Dashboard Warning

When unknown MACs are detected, an orange warning card appears on the dashboard:
- Shows count of unknown devices
- Lists the first 3 with MAC, hostname, and IP
- Clickable — navigates to the MAC Watchlist page

The warning only shows when you have at least one entry in your known list (otherwise it would flag everything).

## Typical Workflow

1. **Initial setup:** Run a UniFi sync or network scan to discover all current devices
2. **Approve all:** Click "Approve All Current" to baseline your network
3. **Ongoing:** After future scans, check the dashboard for unknown devices
4. **Investigate:** When something unknown appears, look at the manufacturer and hostname
5. **Approve or act:** If it's legit, approve it. If not, investigate further.

## Tips

- Run "Approve All Current" after your first full network scan to establish a baseline
- New legitimate devices (guest phones, new IoT gadgets) will show as unknown until approved
- The manufacturer lookup helps identify unknown devices (e.g. "Apple" = someone's iPhone)
- This works best when combined with regular UniFi syncs that keep your IP list fresh
- Unknown MAC alerts are informational — they don't mean something malicious is happening
- Consider running a scan after approving all to verify nothing was missed
