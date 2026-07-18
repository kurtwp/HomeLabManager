# VLAN Features

This document outlines the current VLAN capabilities, known gaps, and planned features for the Home Lab Manager.

---

## Current Capabilities

### Subnet & IP Binding ✅

VLANs are bound to networks (subnets) via the `vlan_id` field on each network record.

- Each network can have a VLAN ID assigned (1–4094)
- The VLAN ID displays as a badge on network cards and detail pages
- When viewing a subnet, the associated VLAN is shown inline
- UniFi sync automatically pulls VLAN IDs from the controller

**Where:** Networks page → each network card shows `VLAN X` badge. Network detail page shows VLAN in the header.

### VLAN Filtering ✅

- Networks can be filtered by VLAN ID via the device type/tag filters
- Search finds networks by name, CIDR, or description (which can include VLAN references)

### VLAN Assignment on Network Creation ✅

When creating a network (manually or via UniFi sync):
- VLAN ID field is available (validated 1–4094)
- Gateway, DNS, DHCP range, description, and notes are all per-network
- Tags can be applied to group networks by function

---

## Gaps (Not Yet Implemented)

### L2 Domains / Routing Domains ❌

**What it is:** Groups VLANs into separate logical Layer 2 domains. This allows reusing identical VLAN IDs (e.g., VLAN 10) across different data centers or isolated office locations without naming or database conflicts.

**Current limitation:** VLAN IDs are stored as a simple integer on the network record. There is no concept of a "domain" that scopes VLAN IDs — so VLAN 10 in "Building A" and VLAN 10 in "Building B" would need different names or descriptions to differentiate them.

**Workaround:** Use network names or tags to distinguish VLANs across locations (e.g., tag "Building A" vs "Building B" on networks that share VLAN IDs).

### Global VLAN Table ❌

**What it is:** A centralized index of all VLANs searchable by VLAN ID number, name, description, or custom tag.

**Current limitation:** There is no dedicated VLAN page. VLANs only appear as attributes on networks. To see all VLANs, you browse the networks list and look at the badges.

**Workaround:** Use the Networks page with visual scanning of VLAN badges, or use the search bar to find networks by description.

### Custom Fields on VLANs ❌

**What it is:** User-defined attributes specifically on a VLAN entity (such as billing codes, support teams, switch fabrics).

**Current limitation:** Custom fields exist for IPs, Devices, and Networks — but not for a dedicated VLAN entity. Since VLANs are an attribute of networks (not their own table), custom fields would attach to the network, not the VLAN directly.

**Workaround:** Use custom fields on the Network entity and add VLAN-specific metadata there (e.g., a custom field called "Billing Code" on the network that uses that VLAN).

---

## Planned Features (Future)

### 1. VLAN Model (First-Class Entity)

Create a dedicated `Vlan` table:
- `id`, `vlan_id` (1–4094), `name`, `description`
- `l2_domain_id` (FK to L2Domain) — for multi-site isolation
- `status` (active, reserved, deprecated)
- Custom fields support
- Link to one or more networks/subnets

### 2. L2 Domains

Create an `L2Domain` table:
- `id`, `name`, `description`, `location`
- Groups VLANs that share the same Layer 2 broadcast domain
- Allows VLAN ID reuse across domains without conflict
- Example: "HQ Campus", "Remote Office", "Data Center A"

### 3. Global VLAN Table Page

A new page (`/vlans`) with:
- Table of all VLANs with ID, name, domain, bound subnets, status
- Search by VLAN ID, name, or description
- Filter by L2 domain or status
- Click to view VLAN detail (associated subnets, IPs, devices)

### 4. VLAN Custom Fields

Extend the custom fields system to support entity_type `vlan`:
- Add VLAN-specific fields (billing code, switch fabric, support team)
- Displayed on VLAN detail page

### 5. VLAN Visualization

- Display VLAN topology showing which subnets are bound to which VLANs
- Show VLAN utilization across L2 domains
- Highlight unused/deprecated VLANs

---

## Current Data Model

```
networks table:
├── id
├── name
├── cidr (e.g., 192.168.10.0/24)
├── vlan_id (INTEGER, nullable) ← VLAN binding
├── gateway
├── dns_servers
├── dhcp_start / dhcp_end
├── description
├── notes
├── parent_id (for nested subnets)
├── is_favorite
├── tags (many-to-many)
└── ip_addresses (one-to-many)
```

VLANs are currently **not** a separate entity — they are an integer attribute on the network record. The planned enhancement would promote VLANs to their own table while maintaining backward compatibility with the existing `vlan_id` field.

---

## UniFi Integration

When syncing from UniFi:
- VLANs are pulled from `ipv4Configuration.vlanId` on each network
- The VLAN ID is stored on the local network record
- UniFi-managed VLANs are imported with their names and subnet bindings

---

## Summary

| Feature | Status | Implementation |
|---------|--------|---------------|
| VLAN binding to subnets | ✅ Done | `Network.vlan_id` field |
| VLAN display on network pages | ✅ Done | Badge on cards and detail |
| VLAN ID validation (1–4094) | ✅ Done | Input validation on create |
| UniFi VLAN sync | ✅ Done | Auto-pulled from controller |
| L2 Domains | ❌ Planned | Requires new model |
| Global VLAN table | ❌ Planned | Requires new page |
| VLAN custom fields | ❌ Planned | Requires entity type extension |
| VLAN visualization | ❌ Planned | Requires new component |
