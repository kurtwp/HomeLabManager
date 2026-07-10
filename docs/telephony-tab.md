# Telephony Tab

The **Telephony** tab is a full PSTN number management system for tracking phone numbers, DID ranges, extensions, and customer assignments. It's accessed via the **Telephony** dropdown in the navigation bar.

## Menu Structure

The Telephony dropdown contains:

| Menu Item | Route | Purpose |
|-----------|-------|---------|
| Dashboard | `/pstn` | Overview with stats and recent numbers |
| Number Ranges | `/pstn/ranges` | Manage blocks of phone numbers |
| Phone Numbers | `/pstn/numbers` | Individual number management |
| Customers | `/pstn/customers` | Customer/tenant tracking |
| Bulk Import | `/pstn/import` | Import numbers from CSV |
| Export | `/pstn/export` | Download data as CSV |
| Audit Trail | `/pstn/audit` | Change history for telephony |

## Dashboard

The telephony dashboard (`/pstn`) provides a high-level overview:

- **Stats cards** — total ranges, total numbers, active, reserved, future use, inactive counts
- **Quick navigation** — buttons to jump to Ranges or Numbers management
- **Recent Numbers** — table of the 10 most recently added phone numbers

## Number Ranges

Ranges represent blocks of sequential phone numbers (e.g. a DID block from your carrier).

### Range Properties

| Field | Description |
|-------|-------------|
| Name | Friendly label (e.g. "Main DID Block") |
| Range Start/End | First and last number in the block |
| Country Code | Country dialing code |
| Area Code | Area/city code |
| Prefix | Number prefix |
| Provider | Carrier name (e.g. AT&T, Twilio) |
| Type | Master or Sub-range |
| Status | Active, Inactive, or Reserved |
| Total Numbers | Count of numbers in the range |

### Range Features

- **Utilization bar** — shows how many numbers in the range are allocated vs available
- **Detail page** — click a range to see all numbers assigned to it
- **Status breakdown** — active, reserved, future use, and inactive counts per range
- **Delete** — removes the range but keeps numbers (they become unlinked)

## Phone Numbers

Individual phone number management with full metadata.

### Number Properties

| Field | Description |
|-------|-------------|
| Number | Full phone number (e.g. +15550101) |
| Extension | Internal extension (e.g. 4501) |
| Type | DID, Extension, Toll-Free, Fax, or Other |
| Status | Active, Inactive, Reserved, or Future Use |
| Assigned To | Person or team name |
| Department | Department name |
| Location | Physical location |
| Device Name | PBX or gateway handling the number |
| Range | Which number range it belongs to |
| Customer | Which customer owns it |
| Description | What the number is used for |
| Notes | Additional notes |

### Filtering Numbers

Five filters available on the numbers page:

- **Search** — free text search across number, name, department
- **Type** — DID, Extension, Toll-Free, Fax, Other
- **Status** — Active, Inactive, Reserved, Future Use
- **Range** — filter by number range
- **Customer** — filter by customer

### Number Actions

- **Add** — create a new number with full details
- **Edit** — inline edit button on each row
- **Delete** — remove individual numbers
- **Delete All** — bulk remove (with confirmation)

## Customers

Track customers or tenants who own phone numbers and ranges.

### Customer Properties

| Field | Description |
|-------|-------------|
| Name | Company or person name |
| Account Number | Optional unique ID |
| Contact Name | Primary contact person |
| Contact Email | Email address |
| Contact Phone | Phone number |
| Notes | Free text notes |

### Customer Detail Page

Clicking a customer name shows:

- Full contact information
- All number ranges assigned to the customer
- All phone numbers assigned to the customer
- Both displayed as sortable tables

## Bulk Import

Import phone numbers from a CSV file at `/pstn/import`.

### CSV Columns

```
number,extension,number_type,status,assigned_to,department,location,device_name,description,notes
```

### Import Options

- **Assign to Range** — optionally link all imported numbers to a range
- **Assign to Customer** — optionally link all imported numbers to a customer
- **Skip duplicates** — checkbox to avoid creating duplicate numbers
- **Template download** — download a pre-filled CSV template to use as a starting point

### Import Results

After upload, shows:
- Count imported
- Count skipped (duplicates)
- Any errors with row numbers

## Export

Download telephony data as CSV at `/pstn/export`. Three export options:

| Export | Contents |
|--------|----------|
| Phone Numbers | All numbers with full details, filterable by range or customer |
| Number Ranges | All ranges with provider and utilization info |
| Customers | All customers with contact details |

## Audit Trail

The PSTN audit trail (`/pstn/audit`) logs all changes made to telephony data:

- **Entity types** — Customer, Range, Number
- **Actions** — Created, Updated, Deleted, Bulk Import
- **Filtering** — by entity type, with configurable result limit (50/100/200)
- **Table view** — timestamp, action, entity type, ID, and details

This is separate from the main History tab and tracks only telephony-specific changes.

## Tips

- Use ranges to organize numbers by carrier block or purpose
- The status field helps plan number allocation: mark numbers as "Future Use" to reserve them
- Assign customers to track multi-tenant number ownership
- Use bulk import for initial setup — prepare your data in a spreadsheet first
- Export regularly as a backup of your telephony inventory
- The audit trail helps track who changed what and when
