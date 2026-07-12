"""Wake-on-LAN service — send magic packets to wake devices."""

import socket
import struct


def send_wol(mac_address: str, broadcast: str = "255.255.255.255", port: int = 9) -> bool:
    """
    Send a Wake-on-LAN magic packet to the specified MAC address.

    Args:
        mac_address: Target MAC (accepts AA:BB:CC:DD:EE:FF, AA-BB-CC-DD-EE-FF, or AABBCCDDEEFF)
        broadcast: Broadcast IP to send the packet to
        port: UDP port (default 9, some use 7)

    Returns:
        True if packet was sent successfully, False on error.
    """
    try:
        # Normalize MAC address
        mac = mac_address.replace(":", "").replace("-", "").replace(".", "").upper()
        if len(mac) != 12:
            raise ValueError(f"Invalid MAC address: {mac_address}")

        # Build magic packet: 6 bytes of 0xFF + MAC repeated 16 times
        mac_bytes = bytes.fromhex(mac)
        magic_packet = b"\xff" * 6 + mac_bytes * 16

        # Send via UDP broadcast
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(magic_packet, (broadcast, port))
        sock.close()

        return True
    except Exception as e:
        print(f"WOL error: {e}")
        return False


def validate_mac_for_wol(mac_address: str | None) -> bool:
    """Check if a MAC address is valid for WOL."""
    if not mac_address:
        return False
    mac = mac_address.replace(":", "").replace("-", "").replace(".", "").upper()
    return len(mac) == 12 and all(c in "0123456789ABCDEF" for c in mac)
