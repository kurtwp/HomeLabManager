# Inventory Export

Generate Ansible or Terraform inventory files from your device and IP data — no manual file maintenance needed.

## Accessing Inventory Export

Click the **wrench icon** (🔧) → **Inventory Export**, or navigate to `/inventory-export`.

## Formats Supported

| Format | File Extension | Use Case |
|--------|:---:|---|
| Ansible INI | `.ini` | Traditional Ansible inventory |
| Ansible YAML | `.yml` | Modern Ansible inventory with host vars |
| Terraform Hosts | `.tf` | `locals` block with host IP lists |
| Terraform Variables | `.tfvars` | Variable file with host lists |

## Data Sources

| Source | Grouping | Description |
|--------|----------|-------------|
| Devices | By device type | Groups like `switch`, `access_point`, `gateway` |
| Active IPs | By network | Groups like `main_lan`, `iot_vlan`, `guest` |

## Options

- **Only devices with IPs** — skip devices that don't have an IP address assigned (enabled by default)

## Workflow

1. Select format and data source
2. Click **Generate** to see a preview
3. Click **Download** to save the file, or **Copy to Clipboard** for quick paste

## Example Output

### Ansible INI
```ini
[access_point]
192.168.2.10  # office_ap  mac=AA:BB:CC:DD:EE:FF
192.168.2.11  # bedroom_ap

[switch]
192.168.2.1  # main_switch  mac=11:22:33:44:55:66
```

### Ansible YAML
```yaml
all:
  children:
    access_point:
      hosts:
        office_ap:
          ansible_host: 192.168.2.10
          mac_address: AA:BB:CC:DD:EE:FF
          manufacturer: Ubiquiti
    switch:
      hosts:
        main_switch:
          ansible_host: 192.168.2.1
```

### Terraform Hosts
```hcl
locals {
  access_point_hosts = [
    "192.168.2.10",
    "192.168.2.11",
  ]

  switch_hosts = [
    "192.168.2.1",
  ]
}
```

### Terraform Variables
```hcl
access_point_hosts = [
  "192.168.2.10",  # office_ap
  "192.168.2.11",  # bedroom_ap
]
```

## Tips

- Use "Devices grouped by type" for infrastructure management (configure switches, APs, servers)
- Use "Active IPs grouped by network" for broader scans or per-VLAN automation
- The generated files use sanitized hostnames (lowercase, underscores, no special chars)
- Re-generate after syncing from UniFi or running scans to keep the inventory current
- The Ansible YAML format includes extra metadata (MAC, manufacturer) as host vars
