"""Input validation utilities."""

import ipaddress
import re


def is_valid_cidr(cidr: str) -> bool:
    """Validate a CIDR notation string."""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def is_valid_ip(ip: str) -> bool:
    """Validate an IP address string."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_valid_mac(mac: str) -> bool:
    """Validate a MAC address (formats: AA:BB:CC:DD:EE:FF or AA-BB-CC-DD-EE-FF)."""
    pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    return bool(re.match(pattern, mac))


def is_valid_vlan_id(vlan_id: int) -> bool:
    """Validate VLAN ID is in the valid range (1-4094)."""
    return 1 <= vlan_id <= 4094


def get_network_info(cidr: str) -> dict:
    """Get useful information about a network CIDR."""
    try:
        net = ipaddress.ip_network(cidr, strict=False)
        return {
            "network_address": str(net.network_address),
            "broadcast_address": str(net.broadcast_address),
            "netmask": str(net.netmask),
            "prefix_length": net.prefixlen,
            "total_addresses": net.num_addresses,
            "usable_hosts": max(net.num_addresses - 2, 0),
            "first_host": str(list(net.hosts())[0]) if net.num_addresses > 2 else None,
            "last_host": str(list(net.hosts())[-1]) if net.num_addresses > 2 else None,
        }
    except ValueError:
        return {}
