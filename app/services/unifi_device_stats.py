"""UniFi device health stats via legacy controller API.

Fetches CPU, RAM, temperature, uptime, and load averages for UniFi devices.
Uses the legacy /proxy/network/api/s/default/stat/device endpoint.
"""

import httpx
from config import UNIFI_API_KEY, UNIFI_BASE_URL


def fetch_device_stats() -> list[dict]:
    """
    Fetch health stats for all UniFi devices.
    Returns list of dicts with stats keyed by MAC address.
    """
    headers = {"X-API-KEY": UNIFI_API_KEY, "Accept": "application/json"}

    try:
        r = httpx.get(
            f"{UNIFI_BASE_URL}/proxy/network/api/s/default/stat/device",
            headers=headers,
            verify=False,
            timeout=15,
        )
        if r.status_code != 200:
            return []
        data = r.json()
        return data.get("data", [])
    except Exception:
        return []


def get_device_health(mac_address: str) -> dict | None:
    """
    Get health stats for a specific device by MAC address.

    Returns dict with:
        - uptime (seconds)
        - uptime_str (human readable)
        - cpu_percent
        - mem_percent
        - mem_used_mb
        - mem_total_mb
        - load_1, load_5, load_15
        - temperatures [{name, type, value}]
        - firmware
        - model
        - state
    """
    all_stats = fetch_device_stats()
    if not all_stats:
        return None

    # Normalize MAC for comparison
    mac_normalized = mac_address.replace(":", "").replace("-", "").upper()

    for device in all_stats:
        dev_mac = (device.get("mac") or "").replace(":", "").replace("-", "").upper()
        if dev_mac == mac_normalized:
            return _extract_health(device)

    return None


def get_all_device_health() -> dict[str, dict]:
    """
    Get health stats for all devices.
    Returns dict keyed by normalized MAC address.
    """
    all_stats = fetch_device_stats()
    result = {}

    for device in all_stats:
        mac = (device.get("mac") or "").replace(":", "").replace("-", "").upper()
        if mac:
            result[mac] = _extract_health(device)

    return result


def _extract_health(device: dict) -> dict:
    """Extract relevant health metrics from a device stat entry."""
    # System stats
    sys_stats = device.get("system-stats") or {}
    sys_detail = device.get("sys_stats") or {}

    # Uptime
    uptime_sec = device.get("uptime") or int(sys_stats.get("uptime", 0))
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    minutes = (uptime_sec % 3600) // 60
    uptime_str = f"{days}d {hours}h {minutes}m"

    # Memory
    mem_total = sys_detail.get("mem_total", 0)
    mem_used = sys_detail.get("mem_used", 0)
    mem_total_mb = round(mem_total / 1024 / 1024) if mem_total else 0
    mem_used_mb = round(mem_used / 1024 / 1024) if mem_used else 0

    # Temperatures
    temperatures = device.get("temperatures") or []

    # PoE power data
    total_max_power = device.get("total_max_power") or device.get("total_max_effective_power") or 0
    total_used_power = device.get("total_used_power") or 0

    # Per-port PoE details
    poe_ports = []

    # Build a map of which device connects to which port on this device
    # by checking all devices' uplink_remote_port
    port_connections = {}  # port_idx -> device name
    all_stats = fetch_device_stats()
    device_mac = (device.get("mac") or "").lower()
    for other_dev in all_stats:
        uplink = other_dev.get("uplink", {})
        if uplink.get("uplink_mac", "").lower().replace(":", "") == device_mac.replace(":", ""):
            remote_port = uplink.get("uplink_remote_port")
            if remote_port:
                port_connections[int(remote_port)] = other_dev.get("name") or "Unknown"

    for port in device.get("port_table", []):
        if port.get("port_poe") and port.get("poe_enable"):
            port_idx = port.get("port_idx")
            port_name = port.get("name", "")

            # Determine connected device: uplink data > port description > generic
            connected_device = port_connections.get(port_idx, "")
            if not connected_device:
                # Fall back to port description (strip -P suffix if present)
                if port_name and "-P" in port_name:
                    connected_device = port_name.split("-P")[0]
                elif port_name and not port_name.startswith("Port"):
                    connected_device = port_name
                else:
                    connected_device = f"Port {port_idx}"

            poe_ports.append({
                "port": port_idx,
                "name": port_name or f"Port {port_idx}",
                "connected_device": connected_device,
                "power_w": float(port.get("poe_power", 0)),
                "voltage": float(port.get("poe_voltage", 0)),
                "current_ma": float(port.get("poe_current", 0)),
                "class": port.get("poe_class", "—"),
                "mode": port.get("poe_mode", "—"),
                "active": port.get("poe_good", False),
            })

    return {
        "name": device.get("name") or device.get("hostname") or "—",
        "model": device.get("model") or "—",
        "state": device.get("state") or "—",
        "firmware": device.get("version") or "—",
        "uptime_sec": uptime_sec,
        "uptime_str": uptime_str,
        "cpu_percent": float(sys_stats.get("cpu", 0)),
        "mem_percent": float(sys_stats.get("mem", 0)),
        "mem_used_mb": mem_used_mb,
        "mem_total_mb": mem_total_mb,
        "load_1": float(sys_detail.get("loadavg_1", 0)),
        "load_5": float(sys_detail.get("loadavg_5", 0)),
        "load_15": float(sys_detail.get("loadavg_15", 0)),
        "temperatures": temperatures,
        "poe_max_power": float(total_max_power),
        "poe_used_power": float(total_used_power),
        "poe_ports": poe_ports,
    }
