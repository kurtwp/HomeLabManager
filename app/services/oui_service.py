"""MAC OUI (Organizationally Unique Identifier) lookup service.

Resolves MAC addresses to manufacturer names using the IEEE OUI database.
"""

from mac_vendor_lookup import MacLookup, InvalidMacError, VendorNotFoundError


# Initialize the lookup object (uses cached OUI database)
_mac_lookup = MacLookup()

# Don't auto-update on import — use cached data (update manually if needed)
# To update: python -c "from mac_vendor_lookup import MacLookup; MacLookup().update_vendors()"


def lookup_manufacturer(mac_address: str) -> str | None:
    """
    Look up the manufacturer/vendor from a MAC address.

    Args:
        mac_address: MAC in any format (AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, AABBCCDDEEFF)

    Returns:
        Manufacturer name (e.g., "Ubiquiti Inc") or None if not found.
    """
    if not mac_address:
        return None
    try:
        return _mac_lookup.lookup(mac_address)
    except (InvalidMacError, VendorNotFoundError):
        return None
    except Exception:
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
