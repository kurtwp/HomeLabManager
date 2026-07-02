# IP Detail vs Device Detail

This document explains the difference between the IP detail page and the Device detail page.

## Overview

- **IPs tab** = "what's on the network" (every address discovered by scans or syncs)
- **Devices tab** = "what hardware I have" (cataloged equipment with details)

An IP points to a device record via `device_id`. An IP without a linked device won't appear in the Devices tab until you set a device type (which creates/links the device record).

## Comparison

| Feature | IP Detail (`/ips/{id}`) | Device Detail (`/devices/{id}`) |
|---------|-------------------------|----------------------------------|
| **Focus** | The IP address | The physical device |
| **Hostname** | ✅ | — |
| **MAC Address** | ✅ | ✅ |
| **Network** | ✅ (which subnet it belongs to) | — |
| **Last Seen** | ✅ | — |
| **Status** | ✅ (Active/Inactive) | — |
| **Assignment Type** | ✅ (Static/DHCP/Reserved) | — |
| **Device Type** | ✅ Dropdown to set/change | Badge showing current type |
| **Manufacturer** | — | ✅ |
| **Model** | — | ✅ |
| **Serial Number** | — | ✅ |
| **All Linked IPs** | — | ✅ (lists all IPs for this device) |
| **Notes** | Per-IP notes (separate) | Per-device notes (separate) |
| **Tags** | Tags on the IP | Tags on the device |
| **Health Stats** | — | ✅ CPU, RAM, temp, uptime (Ubiquiti only) |
| **PoE Power** | — | ✅ Per-port power consumption |
| **Physical Location** | — | ✅ Room, rack, shelf |
| **Custom Fields** | — | ✅ User-defined metadata |

## Notes

- IP notes and device notes are **separate**. Adding a note on the IP detail page does not affect the device detail page, and vice versa.
- Example use: IP notes might say "DHCP lease expires Friday" while device notes might say "Warranty expires 2025, purchased from Amazon."
- The IP detail page is intentionally minimal — it shows network-level information.
- The Device detail page is comprehensive — it shows hardware, health, and management information.

## Linking

When you set a device type on the IP detail page:
1. If a device with the same MAC or hostname already exists → links to it
2. If no match found → creates a new device record and links it
3. The device then appears in the Devices tab
