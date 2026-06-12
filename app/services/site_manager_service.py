"""UniFi Site Manager API service (cloud API at api.ui.com).

Provides cross-site overview: hosts, sites, devices, ISP metrics.
Auth: X-API-KEY header with key from unifi.ui.com → Settings → API Keys.
Base URL: https://api.ui.com/v1
Read-only API.
"""

import httpx
from config import UNIFI_CLOUD_API_KEY


SITE_MANAGER_BASE_URL = "https://api.ui.com/v1"

CLOUD_HEADERS = {
    "X-API-KEY": UNIFI_CLOUD_API_KEY,
    "Accept": "application/json",
}


def is_configured() -> bool:
    """Check if Site Manager API is configured."""
    return bool(UNIFI_CLOUD_API_KEY and UNIFI_CLOUD_API_KEY != "your_cloud_key_here")


def _get_client() -> httpx.Client:
    """Create an httpx client for Site Manager API."""
    return httpx.Client(
        base_url=SITE_MANAGER_BASE_URL,
        headers=CLOUD_HEADERS,
        timeout=15.0,
    )


def test_connection() -> dict:
    """Test the Site Manager API connection."""
    if not is_configured():
        return {
            "success": False,
            "error": "Site Manager API not configured. Set UNIFI_CLOUD_API_KEY in .env "
                     "(get it from unifi.ui.com → Settings → API Keys)",
        }
    try:
        with _get_client() as client:
            r = client.get("/hosts")
            r.raise_for_status()
            data = r.json()
            hosts = data if isinstance(data, list) else data.get("data", [])
            return {
                "success": True,
                "hosts": len(hosts),
            }
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to api.ui.com"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: Check API key"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_hosts() -> list[dict]:
    """Fetch all hosts (controllers) from Site Manager."""
    with _get_client() as client:
        r = client.get("/hosts")
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("data", [])


def fetch_host_by_id(host_id: str) -> dict:
    """Fetch a specific host by ID."""
    with _get_client() as client:
        r = client.get(f"/hosts/{host_id}")
        r.raise_for_status()
        return r.json()


def fetch_sites() -> list[dict]:
    """Fetch all sites across all hosts."""
    with _get_client() as client:
        r = client.get("/sites")
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("data", [])


def fetch_devices() -> list[dict]:
    """Fetch all devices across all sites."""
    with _get_client() as client:
        results = []
        # Paginate if needed
        r = client.get("/devices")
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            results = data
        else:
            results = data.get("data", [])
        return results


def fetch_isp_metrics() -> dict:
    """Fetch ISP health metrics."""
    with _get_client() as client:
        r = client.get("/isp-metrics")
        r.raise_for_status()
        return r.json()
