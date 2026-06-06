# Project Steering — UniFi API Integration

## Project Overview
This project integrates with Ubiquiti UniFi APIs using **Python** and **NiceGUI** for the
frontend, with custom HTML, CSS, and JavaScript for complex UI components.

---

## Confirmed Deployment Details
| Property | Value |
|----------|-------|
| **Controller** | UniFi Dream Machine SE (UDM SE) |
| **Firmware** | UniFi Network 10.4.57 |
| **Console IP** | 192.168.2.254 |
| **Base URL** | `https://192.168.2.254/proxy/network/integration/v1` |
| **Site Name** | Default |
| **Site ID** | `88f7af54-98f8-306a-a1c7-c9349722b1f6` |

> ⚠️ The OpenAPI spec endpoint (`/openapi.json`) is not exposed on this firmware version.
> Use the beezly repo spec `10.2.104.json` as the closest reference — core endpoints are identical.
> Any endpoints added between 10.2.104 → 10.4.57 should be looked up in the official docs.

---

## Tech Stack
- **Backend**: Python
- **Frontend**: NiceGUI + custom HTML / CSS / JavaScript
- **API Source**: beezly/unifi-apis (OpenAPI 3.1.0 specs extracted directly from UniFi controllers)

---

## Primary API Reference (OpenAPI Specs)

> ⭐ Prefer this repo over the official JS-rendered docs — it contains machine-readable
> OpenAPI 3.1.0 JSON specs extracted directly from real UniFi controllers.

**GitHub Repo**: https://github.com/beezly/unifi-apis

### UniFi Network API Specs (use closest version to your controller)
| Version | Raw JSON |
|---------|----------|
| 10.2.104 *(use this — closest available to 10.4.57)* | https://github.com/beezly/unifi-apis/blob/main/unifi-network/10.2.104.json |
| 10.2.97  | https://github.com/beezly/unifi-apis/blob/main/unifi-network/10.2.97.json |
| 10.1.89  | https://github.com/beezly/unifi-apis/blob/main/unifi-network/10.1.89.json |
| 10.1.84  | https://github.com/beezly/unifi-apis/blob/main/unifi-network/10.1.84.json |
| 9.5.21   | https://github.com/beezly/unifi-apis/blob/main/unifi-network/9.5.21.json |

### UniFi Protect API Specs
| Version | Raw JSON |
|---------|----------|
| 7.0.104 *(latest)* | https://github.com/beezly/unifi-apis/blob/main/unifi-protect/7.0.104.json |
| 7.0.94  | https://github.com/beezly/unifi-apis/blob/main/unifi-protect/7.0.94.json |
| 6.2.88  | https://github.com/beezly/unifi-apis/blob/main/unifi-protect/6.2.88.json |

### Official Docs (fallback — JS-rendered, harder to parse)
- Network API: https://developer.ui.com/network/v10.3.58/gettingstarted
- Site Manager API: https://developer.ui.com/site-manager-api/list-hosts

---

## Generating a Python Client from the OpenAPI Spec

The repo supports auto-generating a typed Python client — use this instead of writing raw HTTP
calls where possible:

```bash
pip install openapi-python-client

# Generate Network API client (use version closest to your controller)
openapi-python-client generate \
  --path unifi-network/10.2.104.json \
  --output-path unifi-network-client

# Generate Protect API client
openapi-python-client generate \
  --path unifi-protect/7.0.104.json \
  --output-path unifi-protect-client
```

If not using a generated client, use **`httpx`** with async support (see below).

---

## API Architecture — Two Separate APIs

| | Network API | Site Manager API |
|---|---|---|
| **Scope** | Local per-site control | Cloud, cross-site overview |
| **Base URL** | `https://<console-ip>/integration` | `https://api.ui.com` |
| **Auth header** | `X-API-KEY` | `X-API-KEY` |
| **Key location** | Console → Integrations | unifi.ui.com → Settings → API Keys |
| **OpenAPI spec** | beezly/unifi-apis repo | Not in repo (use official docs) |

> The OpenAPI spec server path is `/integration` — all Network API endpoints are relative to
> `https://<console-ip>/integration/v1/...`

---

## Authentication

### Generating API Keys
- **Network API**: Sign in to your local UniFi console → go to **Integrations** → create an API key
- **Site Manager API**: Sign in at unifi.ui.com → **Settings → API Keys**
- Keys are shown **only once** — store immediately in your `.env` file
- Current Site Manager keys are **read-only**; write access requires a separate key update

### Environment Variables (always use — never hardcode keys)
```bash
# .env
UNIFI_API_KEY=<regenerate_in_console>                    # ⚠️ Regenerate — old key was exposed in chat
UNIFI_BASE_URL=https://192.168.2.254
UNIFI_SITE_ID=88f7af54-98f8-306a-a1c7-c9349722b1f6
UNIFI_CLOUD_API_KEY=your_cloud_key_here  # Site Manager API key
```

```python
import os
from dotenv import load_dotenv

load_dotenv()

UNIFI_API_KEY      = os.environ["UNIFI_API_KEY"]
UNIFI_BASE_URL     = os.environ["UNIFI_BASE_URL"]
UNIFI_SITE_ID      = os.environ["UNIFI_SITE_ID"]
UNIFI_CLOUD_API_KEY = os.environ["UNIFI_CLOUD_API_KEY"]
```

---

## API Conventions (from OpenAPI spec)

### Request Headers
```python
local_headers = {
    "X-API-KEY":    UNIFI_API_KEY,
    "Accept":       "application/json",
    "Content-Type": "application/json",
}

cloud_headers = {
    "X-API-KEY":    UNIFI_CLOUD_API_KEY,
    "Accept":       "application/json",
}
```

### Filtering (Network API list endpoints)
Many GET endpoints support a `filter` query parameter with structured syntax:
```
# Filter syntax: <property>.<function>(<value>)
GET /v1/sites/{siteId}/devices?filter=id.eq(abc123)
GET /v1/sites/{siteId}/clients?filter=name.contains(phone)

# Combine with AND / OR
GET /v1/sites/{siteId}/devices?filter=and(type.eq(ap),state.eq(connected))
```

### Pagination
List endpoints return paginated results. Always handle `offset` and `limit`:
```python
async def get_all_devices(site_id: str) -> list:
    results = []
    offset = 0
    limit = 100
    async with httpx.AsyncClient(base_url=UNIFI_BASE_URL, verify=False) as client:
        while True:
            r = await client.get(
                f"/integration/v1/sites/{site_id}/devices",
                headers=local_headers,
                params={"offset": offset, "limit": limit},
            )
            r.raise_for_status()
            data = r.json()
            results.extend(data.get("data", []))
            if len(data.get("data", [])) < limit:
                break
            offset += limit
    return results
```

---

## Python HTTP Client — httpx (async)

Use **`httpx`** throughout — it's async-compatible with NiceGUI's event loop.

```python
import httpx

# Local Network API call (async)
async def fetch_sites():
    async with httpx.AsyncClient(base_url=UNIFI_BASE_URL, verify=False) as client:
        r = await client.get("/integration/v1/sites", headers=local_headers)
        r.raise_for_status()
        return r.json()

# Site Manager API call (async)
async def fetch_hosts():
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.ui.com/v1/hosts",
            headers=cloud_headers,
        )
        r.raise_for_status()
        return r.json()
```

> **TLS Note**: UniFi local consoles use self-signed certs. `verify=False` is fine for
> local/dev. For production, install the console cert and switch to `verify=True`.

---

## NiceGUI Integration Patterns

- All API calls must be **`async def`** — never block the NiceGUI event loop
- Use `ui.notify()` for success/error feedback
- Disable buttons or show `ui.spinner()` during in-flight requests
- Use `ui.refreshable` for data that updates periodically

```python
from nicegui import ui
import httpx

@ui.page("/devices")
async def devices_page():
    spinner = ui.spinner(size="lg")
    table = ui.table(columns=[], rows=[]).classes("w-full")

    async def load():
        spinner.visible = True
        try:
            data = await fetch_sites()
            table.rows = data.get("data", [])
        except httpx.HTTPStatusError as e:
            ui.notify(f"API error: {e.response.status_code}", type="negative")
        finally:
            spinner.visible = False

    await load()
```

---

## Error Handling

| HTTP Code | Meaning | Action |
|-----------|---------|--------|
| 400 | Bad Request | Check request body / filter syntax |
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Check key permissions / scope |
| 404 | Not Found | Verify endpoint path and site ID |
| 429 | Rate Limited | Backoff and retry with `tenacity` |
| 500 | Server Error | Log and surface to UI |

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def resilient_get(url: str, headers: dict) -> dict:
    async with httpx.AsyncClient(verify=False) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        return r.json()
```

---

## Suggested Project File Structure
```
project/
├── main.py                      # NiceGUI entry point & page routing
├── .env                         # API keys and base URLs (never commit)
├── api/
│   ├── __init__.py
│   ├── client.py                # httpx client setup, shared headers
│   ├── network.py               # Local Network API calls
│   ├── protect.py               # Protect API calls
│   └── site_manager.py          # Cloud Site Manager API calls
├── ui/
│   ├── components/              # Reusable NiceGUI + custom HTML/CSS/JS components
│   └── pages/                   # NiceGUI page definitions
├── unifi-network-client/        # Auto-generated Python client (optional)
└── .kiro/
    └── settings/
        └── mcp.json             # MCP server config for Kiro
```

---

## Kiro MCP Config (`.kiro/settings/mcp.json`)
Enables Kiro to fetch live GitHub spec files on demand during development:
```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"],
      "disabled": false,
      "autoApprove": ["fetch"]
    }
  }
}
```
Use in Kiro chat: `#[fetch] fetch https://github.com/beezly/unifi-apis/blob/main/unifi-network/10.2.104.json`

---

## Key Reminders
- The OpenAPI base path is `/integration` — endpoints are `/integration/v1/...` not `/api/...`
- Always match the spec version to your actual controller firmware version
- Site IDs are UUIDs — fetch them dynamically via `/integration/v1/sites` rather than hardcoding
- The beezly/unifi-apis repo updates automatically when new controller versions are detected
- When an endpoint is unclear, read the OpenAPI JSON spec from the repo — it is the ground truth

