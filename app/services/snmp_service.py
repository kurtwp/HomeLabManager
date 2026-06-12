"""SNMP discovery and device information gathering service.

Uses system snmpget/snmpwalk commands for reliability.
Supports SNMPv1, v2c, and v3.
Requires net-snmp tools installed: snmpget, snmpwalk
"""

import subprocess
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


def _build_snmp_cmd(
    tool: str, ip: str, oid: str,
    community: str = "public", timeout: int = 2, version: str = "2c",
    v3_user: str = "", v3_sec_level: str = "authPriv",
    v3_auth_proto: str = "SHA", v3_auth_pass: str = "",
    v3_priv_proto: str = "AES", v3_priv_pass: str = "",
) -> list[str]:
    """Build the snmpget/snmpwalk command with proper version arguments."""
    output_flag = "-Ovq" if tool == "snmpget" else "-OQn"

    if version == "3":
        cmd = [tool, "-v3", "-t", str(timeout), "-r", "1"]
        cmd += ["-u", v3_user]
        cmd += ["-l", v3_sec_level]
        if v3_sec_level in ("authNoPriv", "authPriv"):
            cmd += ["-a", v3_auth_proto, "-A", v3_auth_pass]
        if v3_sec_level == "authPriv":
            cmd += ["-x", v3_priv_proto, "-X", v3_priv_pass]
        cmd += [output_flag, ip, oid]
    else:
        version_flag = "1" if version == "1" else "2c"
        cmd = [tool, f"-v{version_flag}", "-c", community,
               "-t", str(timeout), "-r", "1", output_flag, ip, oid]
    return cmd


def _run_snmpget(ip: str, oid: str, **kwargs) -> str | None:
    """Run snmpget command and return the value."""
    try:
        cmd = _build_snmp_cmd("snmpget", ip, oid, **kwargs)
        timeout = kwargs.get("timeout", 2)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 3)
        if result.returncode == 0 and result.stdout.strip():
            value = result.stdout.strip().strip('"')
            if "No Such" in value or "Timeout" in value:
                return None
            return value
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def _run_snmpwalk(ip: str, oid: str, **kwargs) -> list[tuple[str, str]]:
    """Run snmpwalk command and return list of (oid, value) tuples."""
    results = []
    try:
        cmd = _build_snmp_cmd("snmpwalk", ip, oid, **kwargs)
        timeout = kwargs.get("timeout", 2)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
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


def get_device_info(ip: str, **kwargs) -> SNMPDeviceInfo:
    """
    Query a device via SNMP and gather system information.

    Args:
        ip: Target IP address
        **kwargs: SNMP settings (community, timeout, version, v3_user, etc.)

    Returns:
        SNMPDeviceInfo with all gathered data
    """
    info = SNMPDeviceInfo(ip=ip)

    # Test reachability with sysDescr
    sys_descr = _run_snmpget(ip, OIDS["sysDescr"], **kwargs)
    if sys_descr is None:
        info.error = "SNMP not reachable (timeout or credentials mismatch)"
        return info

    info.reachable = True
    info.sys_descr = sys_descr

    # Get system info
    info.sys_name = _run_snmpget(ip, OIDS["sysName"], **kwargs) or ""
    info.sys_location = _run_snmpget(ip, OIDS["sysLocation"], **kwargs) or ""
    info.sys_contact = _run_snmpget(ip, OIDS["sysContact"], **kwargs) or ""
    info.sys_object_id = _run_snmpget(ip, OIDS["sysObjectID"], **kwargs) or ""

    # Uptime
    uptime_raw = _run_snmpget(ip, OIDS["sysUpTime"], **kwargs)
    if uptime_raw:
        info.sys_uptime = uptime_raw

    # Interface count
    if_num = _run_snmpget(ip, OIDS["ifNumber"], **kwargs)
    if if_num:
        try:
            info.interface_count = int(if_num)
        except ValueError:
            pass

    # Get interface details via snmpwalk
    iface_descriptions = _run_snmpwalk(ip, OIDS["ifDescr"], **kwargs)
    iface_statuses = _run_snmpwalk(ip, OIDS["ifOperStatus"], **kwargs)
    iface_speeds = _run_snmpwalk(ip, OIDS["ifSpeed"], **kwargs)
    iface_macs = _run_snmpwalk(ip, OIDS["ifPhysAddress"], **kwargs)

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


def scan_network_snmp(ip_list: list[str], **kwargs) -> list[SNMPDeviceInfo]:
    """
    Scan a list of IPs for SNMP-enabled devices.

    Args:
        ip_list: List of IP addresses to probe
        **kwargs: SNMP settings (community, timeout, version, v3_user, etc.)

    Returns:
        List of SNMPDeviceInfo for devices that responded
    """
    results = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(get_device_info, ip, **kwargs): ip
            for ip in ip_list
        }
        for future in as_completed(futures):
            info = future.result()
            if info.reachable:
                results.append(info)

    return results
