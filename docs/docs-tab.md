# Docs Tab (Knowledge Base)

The **Docs** tab is an internal knowledge base for your home lab. Write and organize articles, runbooks, how-tos, and troubleshooting guides — all stored alongside your network data and accessible from the same interface.

## Accessing the Docs Tab

Click **Docs** in the top navigation bar, or navigate to `/docs`.

## Article List

The main view shows all articles sorted by last updated, with each card displaying:

- **Category badge** — color-coded (How To, Troubleshooting, Runbook, General)
- **Title** — clickable to open the full article
- **Preview** — first 150 characters of the article body

### Filtering by Category

Use the **Category** dropdown to filter articles:

| Category | Color | Use For |
|----------|-------|---------|
| How To | Blue | Step-by-step procedures |
| Troubleshooting | Orange | Problem/solution guides |
| Runbook | Green | Operational procedures and checklists |
| General | Gray | Everything else |

## Creating Articles

### New Article

Click **New Article** to open a full-screen editor with:

- **Title** — required
- **Category** — select from the four categories
- **Body** — Markdown editor with Edit/Preview tabs
- Live preview renders the Markdown as you type

### New from Template

Click **New from Template** to create an article pre-filled with a structured template. Templates provide a starting framework so you don't have to start from scratch. Available templates are defined in the system and cover common documentation patterns.

## Article Detail Page

Clicking an article navigates to `/docs/{id}`, which provides:

### View Tab
- Full rendered Markdown content
- Category badge and title

### Edit Tab
- Edit the title and body
- Save changes in place

### Actions
- **Back arrow** — return to the article list
- **Delete** — permanently remove the article (no confirmation undo)

## Article Data Model

Each article contains:

| Field | Description |
|-------|-------------|
| Title | Article heading (required) |
| Body | Markdown content |
| Category | One of: how-to, troubleshooting, runbook, general |
| Linked IP | Optional link to a specific IP address |
| Linked Device | Optional link to a specific device |
| Linked Network | Optional link to a specific network |
| Created At | Timestamp |
| Updated At | Auto-updated on save |

The optional entity links allow articles to be associated with specific infrastructure items, enabling context-aware documentation.

## Writing in Markdown

The body field supports full Markdown syntax:

- Headings (`#`, `##`, `###`)
- Bold, italic, code
- Bullet and numbered lists
- Code blocks with syntax highlighting
- Links and images
- Tables

The Edit/Preview tabs let you switch between writing and seeing the rendered result.

## Tips

- Use **Runbook** category for procedures you repeat (firmware upgrades, backup steps)
- Use **Troubleshooting** for common issues and their resolutions
- Use **How To** for setup guides and configuration walkthroughs
- Keep articles focused — one topic per article makes them easier to find
- Link articles to specific devices or networks when the content is specific to that item
- The knowledge base is searchable via the global search bar
