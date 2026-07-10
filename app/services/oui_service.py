"""MAC OUI (Organizationally Unique Identifier) lookup service.

Resolves MAC addresses to manufacturer names using a local vendor database file.
"""

import os

# Load vendor database into memory at import time
_oui_db: dict[str, str] = {}

_vendor_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "mac-vendors.txt")

if os.path.exists(_vendor_file):
    with open(_vendor_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Format: PREFIX:Vendor Name (colon-separated, first colon is delimiter)
                colon_idx = line.find(":")
                if colon_idx > 0:
                    prefix = line[:colon_idx].strip().upper()
                    vendor = line[colon_idx + 1:].strip()
                    if prefix and vendor:
                        _oui_db[prefix] = vendor


def lookup_manufacturer(mac_address: str) -> str | None:
    """
    Look up the manufacturer/vendor from a MAC address.

    Args:
        mac_address: MAC in any format (AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF)

    Returns:
        Manufacturer name (e.g., "Ubiquiti Inc") or None if not found.
    """
    if not mac_address or not _oui_db:
        return None

    # Normalize MAC — strip separators and uppercase
    mac_clean = mac_address.replace(":", "").replace("-", "").replace(".", "").upper()

    # Try 6-char prefix first (most common OUI), then 9, then 7
    for prefix_len in [6, 9, 7, 8]:
        prefix = mac_clean[:prefix_len]
        if prefix in _oui_db:
            return _oui_db[prefix]

    return None


def lookup_bulk(mac_addresses: list[str]) -> dict[str, str | None]:
    """
    Look up manufacturers for a list of MAC addresses.

    Returns:
        Dict mapping MAC → manufacturer name (or None).
    """
    results = {}
    for mac in mac_addresses:
        results[mac] = lookup_manufacturer(mac)
    return results
