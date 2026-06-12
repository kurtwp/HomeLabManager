"""SNMP discovery and device information gathering service.

Uses system snmpget/snmpwalk commands for reliability (avoids pysnmp dependency issues).
Requires net-snmp tools installed: snmpget, snmpwalk
"""

import subprocess
import re
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


# Common SNMP OIDs
OIDS = {
    "sysDescr": "1.3.6.1.2.1.1.1.0",
    "sysObjectID": "1.3.6.1.2.1.1.2.0",
    "sysUpTime": "1.3.6.1.2.1.1.3.0",
    "sysContact": "1.3.6.1.2.1.1.4.0",
    "sysName": "1.3.6.1.2.1.1.5.0",
    "sysLocation": "1.3.6.1.2.1.1.6.0",
    "ifNumber": "1.3.6.1.2.1.2.1.0",
    # IF-MIB interface table
    "ifDescr": "1.3.6.1.2.1.2.2.1.2",
    "ifSpeed": "1.3.6.1.2.1.2.2.1.5",
    "ifPhysAddress": "1.3.6.1.2.1.2.2.1.6",
    "ifOperStatus": "1.3.6.1.2.1.2.2.1.8",
}


@dataclass
class SNMPDeviceInfo:
    """Information gathered from a device via SNMP."""
    ip: str
    reachable: bool = False
    sys_name: str = ""
    sys_descr: str = ""
    sys_location: str = ""
    sys_contact: str = ""
    sys_uptime: str = ""
    sys_object_id: str = ""
    interface_count: int = 0
    interfaces: list = field(default_factory=list)
    error: str = ""


def _run_snmpget(ip: str, oid: str, community: str = "public", timeout: int = 2) -> str | None:
    """Run snmpget command and return the value."""
    try:
        result = subprocess.run(
            ["snmpget", "-v2c", "-c", community, "-t", str(timeout), "-r", "1",
             "-Ovq", ip, oid],
            capture_output=True, text=True, timeout=timeout + 3,
        )
        if result.returncode == 0 and result.stdout.strip():
            value = result.stdout.strip().strip('"')
            if "No Such" in value or "Timeout" in value:
                return None
            return value
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _run_snmpwalk(ip: str, oid: str, community: str = "public", timeout: int = 2) -> list[tuple[str, str]]:
    """Run snmpwalk command and return list of (oid, value) tuples."""
    results = []
    try:
        result = subprocess.run(
            ["snmpwalk", "-v2c", "-c", community, "-t", str(timeout), "-r", "1",
             "-OQn", ip, oid],
            capture_output=True, text=True, timeout=timeout + 10,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if " = " in line:
                    parts = line.split(" = ", 1)
                    oid_str = parts[0].strip()
                    val = parts[1].strip().strip('"') if len(parts) > 1 else ""
                    if "No Such" not in val and "No more" not in val:
                        results.append((oid_str, val))
    except (subprocess.TimeoutExpired, OSError):
        pass
    return results


def get_device_info(ip: str, community: str = "public", timeout: int = 3) -> SNMPDeviceInfo:
    """
    Query a device via SNMP and gather system information.

    Args:
        ip: Target IP address
        community: SNMP community string (default: "public")
        timeout: Timeout in seconds per request

    Returns:
        SNMPDeviceInfo with all gathered data
    """
    info = SNMPDeviceInfo(ip=ip)

    # Test reachability with sysDescr
    sys_descr = _run_snmpget(ip, OIDS["sysDescr"], community, timeout)
    if sys_descr is None:
        info.error = "SNMP not reachable (timeout or community string mismatch)"
        return info

    info.reachable = True
    info.sys_descr = sys_descr

    # Get system info
    info.sys_name = _run_snmpget(ip, OIDS["sysName"], community, timeout) or ""
    info.sys_location = _run_snmpget(ip, OIDS["sysLocation"], community, timeout) or ""
    info.sys_contact = _run_snmpget(ip, OIDS["sysContact"], community, timeout) or ""
    info.sys_object_id = _run_snmpget(ip, OIDS["sysObjectID"], community, timeout) or ""

    # Uptime
    uptime_raw = _run_snmpget(ip, OIDS["sysUpTime"], community, timeout)
    if uptime_raw:
        # snmpget returns uptime like "(12345) 0:02:03.45" or just ticks
        info.sys_uptime = uptime_raw

    # Interface count
    if_num = _run_snmpget(ip, OIDS["ifNumber"], community, timeout)
    if if_num:
        try:
            info.interface_count = int(if_num)
        except ValueError:
            pass

    # Get interface details via snmpwalk
    iface_descriptions = _run_snmpwalk(ip, OIDS["ifDescr"], community, timeout)
    iface_statuses = _run_snmpwalk(ip, OIDS["ifOperStatus"], community, timeout)
    iface_speeds = _run_snmpwalk(ip, OIDS["ifSpeed"], community, timeout)
    iface_macs = _run_snmpwalk(ip, OIDS["ifPhysAddress"], community, timeout)

    # Build lookup maps keyed by interface index
    def _get_index(oid_str: str) -> str:
        return oid_str.rsplit(".", 1)[-1] if "." in oid_str else ""

    status_map = {_get_index(oid): val for oid, val in iface_statuses}
    speed_map = {_get_index(oid): val for oid, val in iface_speeds}
    mac_map = {_get_index(oid): val for oid, val in iface_macs}

    for oid, descr in iface_descriptions:
        idx = _get_index(oid)

        status_val = status_map.get(idx, "")
        if status_val == "1" or "up" in status_val.lower():
            status = "up"
        elif status_val == "2" or "down" in status_val.lower():
            status = "down"
        else:
            status = status_val

        speed_val = speed_map.get(idx, "0")
        try:
            speed_int = int(speed_val)
            if speed_int >= 1_000_000_000:
                speed_str = f"{speed_int // 1_000_000_000} Gbps"
            elif speed_int >= 1_000_000:
                speed_str = f"{speed_int // 1_000_000} Mbps"
            elif speed_int > 0:
                speed_str = f"{speed_int // 1000} Kbps"
            else:
                speed_str = ""
        except (ValueError, TypeError):
            speed_str = speed_val

        mac_val = mac_map.get(idx, "")

        info.interfaces.append({
            "index": idx,
            "name": descr,
            "status": status,
            "speed": speed_str,
            "mac": mac_val,
        })

    return info


def scan_network_snmp(
    ip_list: list[str],
    community: str = "public",
    timeout: int = 2,
) -> list[SNMPDeviceInfo]:
    """
    Scan a list of IPs for SNMP-enabled devices.

    Args:
        ip_list: List of IP addresses to probe
        community: SNMP community string
        timeout: Timeout per device

    Returns:
        List of SNMPDeviceInfo for devices that responded
    """
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(get_device_info, ip, community, timeout): ip
            for ip in ip_list
        }
        for future in as_completed(futures):
            info = future.result()
            if info.reachable:
                results.append(info)

    return results
