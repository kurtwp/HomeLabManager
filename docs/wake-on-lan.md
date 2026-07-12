# Wake-on-LAN

The **Wake-on-LAN (WOL)** feature lets you remotely power on devices from their detail page by sending a magic packet.

## How It Works

Wake-on-LAN sends a special "magic packet" (6 bytes of `0xFF` followed by the target MAC address repeated 16 times) via UDP broadcast. The target device's network interface listens for this packet while in standby/sleep and powers the machine on.

## Using WOL

1. Navigate to a device detail page (`/devices/{id}`)
2. If the device has a valid MAC address, a green **Wake on LAN** button appears below the header
3. Click the button to send the magic packet
4. A notification confirms whether the packet was sent

## Requirements

- The target device must have WOL enabled in its BIOS/UEFI
- The device's network interface must support WOL (most modern NICs do)
- The device must be on the same broadcast domain (same VLAN/subnet) as the server running this app
- The device must have a MAC address stored in its record

## Limitations

- WOL only works within the local broadcast domain — it won't cross routers/VLANs unless you configure directed broadcast
- There's no way to confirm the device actually woke up from the packet alone — use uptime monitoring to verify
- The device must be in standby/sleep (S3/S4/S5), not fully powered off at the PSU

## Tips

- Pair WOL with uptime monitoring to verify the device comes online after sending the packet
- Works great for servers, NAS devices, and workstations that don't need to run 24/7
- If WOL doesn't work, check: BIOS WOL setting, NIC driver WOL setting, and that the device is on the same subnet
