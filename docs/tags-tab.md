# Tags Tab

The **Tags** tab lets you create and manage color-coded labels that can be applied across your entire inventory — IPs, devices, and networks. Tags provide a flexible, cross-cutting way to organize and filter your infrastructure.

## Accessing the Tags Tab

Click **Tags** in the top navigation bar, or navigate to `/tags`.

## Tag List

The main view displays all tags as cards in a grid layout. Each card shows:

- **Color swatch** — the tag's assigned color as a circle
- **Name** — the tag label (always lowercase)
- **Usage counts** — how many IPs, devices, and networks use this tag
- **Edit button** — modify name or color
- **Delete button** — remove the tag (with confirmation)

## Creating a Tag

Click **New Tag** to open the creation dialog:

| Field | Required | Description |
|-------|----------|-------------|
| Tag Name | Yes | A short label (stored lowercase, e.g. "production", "iot", "critical") |
| Color | Yes | Hex color picked from a color chooser (defaults to blue #1976d2) |

Tag names must be unique — duplicates are rejected.

## Editing a Tag

Click the edit (pencil) icon on any tag card to modify:

- **Name** — rename the tag (updates everywhere it's used)
- **Color** — change the display color

## Deleting a Tag

Click the delete (trash) icon to remove a tag. A confirmation dialog warns that the tag will be removed from all associated items. Deleting a tag does not delete the items it was applied to — it only removes the label.

## Where Tags Are Used

Tags can be assigned to three entity types:

| Entity | Where to Assign |
|--------|----------------|
| IP Addresses | IP detail page (`/ips/{id}`) |
| Devices | Device detail page (`/devices/{id}`) |
| Networks | Network detail page (`/networks/{id}`) |

### How Tags Appear

Tags show up as color-coded chips throughout the application:
- On device cards in the Devices list
- On IP cards in the IPs list
- On network cards in the Networks list
- In the Dashboard's recently modified section
- In filter dropdowns on the IPs, Devices, and Networks pages

### Filtering by Tag

Multiple pages support tag-based filtering:
- **IPs page** — "Tag" dropdown filter
- **Devices page** — "Tag" dropdown filter
- **Networks page** — "Filter by Tag" dropdown

## Tag Data Model

| Field | Type | Description |
|-------|------|-------------|
| Name | String (100) | Unique, lowercase label |
| Color | String (7) | Hex color code (e.g. `#1976d2`) |

Tags are connected to entities via many-to-many relationships:
- `ip_tags` — links tags to IP addresses
- `device_tags` — links tags to devices
- `network_tags` — links tags to networks

## Tips

- Use descriptive, short names: "critical", "guest", "iot", "needs-upgrade", "floor-2"
- Choose distinct colors for tags you'll use frequently — it makes scanning lists faster
- Tags work great for cross-cutting concerns that don't fit into type/category hierarchies
- Combine tags with type filters for powerful multi-dimensional filtering
- Check usage counts before deleting a tag to understand the impact
- Tags are shared across all entity types, so "production" on a network and "production" on a device are the same tag
