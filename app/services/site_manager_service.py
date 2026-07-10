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


def fetch_devices() -> tuple[list[dict], list[dict]]:
    """Fetch all devices across all sites (flattened from host groupings).
    
    Returns:
        Tuple of (current_devices, old_devices) — deduplicated by MAC.
        Current = online or from named host. Old = stale/duplicate entries.
    """
    with _get_client() as client:
        r = client.get("/devices")
        r.raise_for_status()
        data = r.json()
        raw_list = data if isinstance(data, list) else data.get("data", [])

        # The API returns [{hostId, hostName, devices: [...]}, ...]
        # Flatten into a single device list with hostName attached
        all_devices = []
        for entry in raw_list:
            host_name = entry.get("hostName") or entry.get("hostId", "Unknown")
            devices = entry.get("devices", [])
            if isinstance(devices, list):
                for dev in devices:
                    dev["_hostName"] = host_name
                    all_devices.append(dev)
            else:
                all_devices.append(entry)

        # Separate current vs old by MAC
        # Current = online or from a named host; Old = stale duplicates
        seen_macs = {}
        old_devices = []
        for dev in all_devices:
            mac = dev.get("mac", "")
            if mac in seen_macs:
                existing = seen_macs[mac]
                # Decide which is current, which is old
                if dev.get("status") == "online" and existing.get("status") != "online":
                    old_devices.append(existing)
                    seen_macs[mac] = dev
                elif dev.get("_hostName", "").isalpha() and not existing.get("_hostName", "").isalpha():
                    old_devices.append(existing)
                    seen_macs[mac] = dev
                else:
                    old_devices.append(dev)
            else:
                seen_macs[mac] = dev

        current_devices = list(seen_macs.values())
        return current_devices, old_devices


def fetch_isp_metrics() -> dict:
    """Fetch ISP health metrics. Uses /v1/isp-metrics/{type} endpoint."""
    # type = "5m" for 5-minute intervals or "1h" for hourly
    try:
        r = httpx.get(
            "https://api.ui.com/v1/isp-metrics/5m",
            headers=CLOUD_HEADERS,
            timeout=15.0,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass

    return {"error": "ISP metrics endpoint not available. This feature may require EA access or a specific firmware version."}
