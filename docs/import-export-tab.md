# Import/Export Tab

The **Import/Export** tab lets you back up your data or migrate it into the system using CSV files. It supports exporting IPs and devices, and importing IP addresses from CSV into any network.

## Accessing the Import/Export Tab

Click **Import/Export** in the top navigation bar, or navigate to `/import-export`.

## Export Data

The export section lets you download CSV files of your inventory for backup, reporting, or use in other tools.

### Export IPs

Downloads a CSV of all IP addresses with full details.

- **Network filter** — optionally scope the export to a single network/subnet, or export all
- Output file: `ip_addresses.csv`

### Export Devices

Downloads a CSV of all devices with their properties.

- Includes name, type, manufacturer, model, serial, MAC, location info
- Output file: `devices.csv`

## Import IPs from CSV

Upload a CSV file to bulk-add IP addresses into a chosen network.

### CSV Format

The CSV must have a header row with the following columns:

| Column | Required | Values |
|--------|----------|--------|
| address | Yes | IP address (e.g. `192.168.1.100`) |
| hostname | No | DNS name or label |
| mac_address | No | MAC in `AA:BB:CC:DD:EE:FF` format |
| assignment_type | No | `static`, `dhcp`, or `reserved` |
| notes | No | Free text |

### Import Behavior

- **Target Network** — select which network the imported IPs should belong to (required)
- **Duplicate handling** — existing IPs (same address) are automatically skipped
- **File size limit** — 5 MB maximum
- **Results** — after upload, shows count of added, skipped, and any errors

### Import Steps

1. Select the target network from the dropdown
2. Click "Upload CSV" or drag a `.csv` file into the upload area
3. The import runs automatically on upload
4. Review the results summary (added / skipped / errors)

## Tips

- Export before making bulk changes — it's your undo safety net
- Use the network filter on export to get a focused CSV of just one subnet
- The import is safe to run repeatedly — duplicates are skipped, not overwritten
- You can export from one network and re-import into another for migration
- CSV files can be opened and edited in Excel, LibreOffice Calc, or any text editor
