# IP Conflict Detection

The **Conflict Detection** feature automatically scans for duplicate IP addresses and MAC address conflicts across your network inventory and displays warnings on the dashboard.

## What It Detects

### IP Conflicts
Multiple active entries with the same IP address. This can happen when:
- Two devices are statically assigned the same IP
- A DHCP lease conflicts with a static assignment
- Stale entries weren't cleaned up after a re-IP

### MAC Conflicts
The same MAC address appearing on multiple active IPs within the same network. This indicates:
- A device changed its IP but the old entry wasn't updated
- ARP spoofing or a misconfigured device
- Duplicate scan results from different sources

Note: A single MAC with multiple IPs on *different* networks is normal (e.g. a router with interfaces on multiple VLANs) and is not flagged.

## Where Conflicts Appear

### Dashboard
When conflicts are detected, a red-bordered warning card appears on the main dashboard showing:
- Total number of conflicts
- The first few IP conflicts (address + entry count)
- The first few MAC conflicts (MAC + IP count)

This gives you immediate visibility without having to check a separate page.

## Conflict Details Shown

For each IP conflict:
- The duplicated address
- Number of entries
- Hostname, MAC, network, source, and last-seen for each entry

For each MAC conflict:
- The duplicated MAC address
- Number of IPs using it on the same network
- Address, hostname, network, and source for each entry

## Resolution

Conflicts must be resolved manually since the system can't determine which entry is correct:

1. Navigate to the IPs page (`/ips`)
2. Find the conflicting entries
3. Delete the stale/incorrect entry, or update it to the correct values

## Tips

- Run a UniFi sync or network scan, then check the dashboard for new conflicts
- IP conflicts often indicate a DHCP exhaustion issue where static IPs overlap with the DHCP range
- Set DHCP ranges on your networks to help the system classify IPs correctly and avoid overlaps
- MAC conflicts on the same subnet usually mean stale data — delete the older entry
