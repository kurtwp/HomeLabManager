"""UniFi Network API integration service.

Uses the Integration API on the local UDM SE console.
Base URL: https://<console-ip>/proxy/network/integration/v1
Auth: X-API-KEY header
"""

import httpx
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from config import UNIFI_API_KEY, UNIFI_BASE_URL, UNIFI_SITE_ID
from app.models.network import Network
from app.models.ip_address import IPAddress, AssignmentType, IPStatus
from app.models.device import Device, DeviceType
from app.models.changelog import EntityType, ActionType
from app.services.changelog_service import log_change


# --- HTTP Client Helpers ---

UNIFI_HEADERS = {
    "X-API-KEY": UNIFI_API_KEY,
    "Accept": "application/json",
    "Content-Type": "application/json",
}

BASE_INTEGRATION_URL = f"{UNIFI_BASE_URL}/proxy/network/integration/v1"


def _get_client() -> httpx.Client:
    """Create an httpx client for UniFi API calls."""
    return httpx.Client(
        base_url=BASE_INTEGRATION_URL,
        headers=UNIFI_HEADERS,
        verify=False,  # Self-signed cert on local console
        timeout=30.0,
    )


def is_configured() -> bool:
    """Check if UniFi integration is configured."""
    return bool(UNIFI_API_KEY and UNIFI_BASE_URL and UNIFI_SITE_ID)


# --- API Endpoints ---

def fetch_sites() -> list[dict]:
    """Fetch all sites from the UniFi controller."""
    with _get_client() as client:
        r = client.get("/sites")
        r.raise_for_status()
        return r.json().get("data", [])


def fetch_devices_from_unifi() -> list[dict]:
    """Fetch all network devices (APs, switches, gateways) from UniFi."""
    with _get_client() as client:
        results = []
        offset = 0
        limit = 100
        while True:
            r = client.get(
                f"/sites/{UNIFI_SITE_ID}/devices",
                params={"offset": offset, "limit": limit},
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            results.extend(data)
            if len(data) < limit:
                break
            offset += limit
        return results


def fetch_clients_from_unifi() -> list[dict]:
    """Fetch all active clients from UniFi."""
    with _get_client() as client:
        results = []
        offset = 0
        limit = 100
        while True:
            r = client.get(
                f"/sites/{UNIFI_SITE_ID}/clients",
                params={"offset": offset, "limit": limit},
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            results.extend(data)
            if len(data) < limit:
                break
            offset += limit
        return results


def fetch_networks_from_unifi() -> list[dict]:
    """Fetch all networks/VLANs configured on the UniFi controller."""
    with _get_client() as client:
        results = []
        offset = 0
        limit = 100
        while True:
            r = client.get(
                f"/sites/{UNIFI_SITE_ID}/networks",
                params={"offset": offset, "limit": limit},
            )
            r.raise_for_status()
            data = r.json().get("data", [])
            results.extend(data)
            if len(data) < limit:
                break
            offset += limit

        # For each network, try to fetch full details which may include subnet
        detailed_results = []
        for net in results:
            net_id = net.get("id")
            if net_id:
                try:
                    detail_r = client.get(f"/sites/{UNIFI_SITE_ID}/networks/{net_id}")
                    if detail_r.status_code == 200:
                        detailed_results.append(detail_r.json())
                    else:
                        detailed_results.append(net)
                except Exception:
                    detailed_results.append(net)
            else:
                detailed_results.append(net)

        return detailed_results


# --- Sync Operations ---

def sync_networks(session: Session) -> dict:
    """
    Pull networks/VLANs from UniFi and create/update local records.
    Returns summary of actions taken.
    """
    unifi_networks = fetch_networks_from_unifi()
    created = 0
    updated = 0
    skipped = 0
    errors = []

    for unet in unifi_networks:
        try:
            name = unet.get("name", "Unnamed Network")
            # UniFi Integration API may use different field names depending on version
            # Try multiple possible fields for subnet/CIDR
            subnet = (
                unet.get("subnet")
                or unet.get("ipSubnet")
                or unet.get("ip_subnet")
            )

            # Check ipv4Configuration object (UniFi Integration API v1)
            if not subnet and unet.get("ipv4Configuration"):
                ipv4_config = unet["ipv4Configuration"]
                if isinstance(ipv4_config, dict):
                    subnet = (
                        ipv4_config.get("subnet")
                        or ipv4_config.get("cidr")
                        or ipv4_config.get("ipSubnet")
                    )
                    # hostIpAddress + prefixLength (actual UniFi format)
                    if not subnet and ipv4_config.get("hostIpAddress") and ipv4_config.get("prefixLength"):
                        import ipaddress
                        try:
                            net = ipaddress.ip_network(
                                f"{ipv4_config['hostIpAddress']}/{ipv4_config['prefixLength']}",
                                strict=False
                            )
                            subnet = str(net)
                        except ValueError:
                            pass
                    # Try gateway + prefix
                    if not subnet and ipv4_config.get("gateway") and ipv4_config.get("prefixLength"):
                        import ipaddress
                        try:
                            net = ipaddress.ip_network(
                                f"{ipv4_config['gateway']}/{ipv4_config['prefixLength']}",
                                strict=False
                            )
                            subnet = str(net)
                        except ValueError:
                            pass

            # Some responses include separate ip + netmask
            if not subnet and unet.get("ip") and unet.get("netmask"):
                import ipaddress
                try:
                    net = ipaddress.ip_network(f"{unet['ip']}/{unet['netmask']}", strict=False)
                    subnet = str(net)
                except ValueError:
                    pass

            # Check inside metadata object
            if not subnet and unet.get("metadata"):
                meta = unet["metadata"]
                if isinstance(meta, dict):
                    subnet = (
                        meta.get("subnet")
                        or meta.get("ipSubnet")
                        or meta.get("ip_subnet")
                        or meta.get("cidr")
                    )

            # Try gatewayIp at top level as last resort
            if not subnet and unet.get("gatewayIp"):
                import ipaddress
                try:
                    net = ipaddress.ip_network(f"{unet['gatewayIp']}/24", strict=False)
                    subnet = str(net)
                except ValueError:
                    pass

            vlan_id = unet.get("vlanId") or unet.get("vlan") or unet.get("vlan_id")

            # Extract gateway from ipv4Configuration
            gateway = None
            if unet.get("ipv4Configuration") and isinstance(unet["ipv4Configuration"], dict):
                gateway = unet["ipv4Configuration"].get("hostIpAddress")

            if not subnet:
                skipped += 1
                ipv4_info = str(unet.get("ipv4Configuration", ""))[:200]
                meta_info = str(unet.get("metadata", ""))[:100]
                errors.append(
                    f"Network '{name}': no subnet found "
                    f"(ipv4Config: {ipv4_info}, metadata: {meta_info})"
                )
                continue

            # Normalize CIDR (ensure it has a prefix length)
            if "/" not in subnet:
                subnet = f"{subnet}/24"

            # Check if network already exists by CIDR or by name
            existing = session.query(Network).filter(Network.cidr == subnet).first()
            if not existing:
                existing = session.query(Network).filter(Network.name == name).first()

            if existing:
                # Update name/vlan if changed
                changed = False
                if existing.name != name:
                    existing.name = name
                    changed = True
                if vlan_id and existing.vlan_id != vlan_id:
                    existing.vlan_id = vlan_id
                    changed = True
                if changed:
                    updated += 1
            else:
                new_net = Network(
                    name=name,
                    cidr=subnet,
                    vlan_id=vlan_id,
                    gateway=gateway,
                    description=f"Imported from UniFi ({unet.get('id', '')})",
                )
                session.add(new_net)
                session.flush()
                log_change(
                    session,
                    entity_type=EntityType.NETWORK,
                    entity_id=new_net.id,
                    action=ActionType.CREATED,
                    entity_name=name,
                    new_values={"cidr": subnet, "vlan_id": vlan_id, "source": "unifi_sync"},
                    comment="Imported from UniFi controller",
                )
                created += 1
        except Exception as e:
            errors.append(f"Network '{unet.get('name', '?')}': {e}")

    session.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}


def sync_devices(session: Session) -> dict:
    """
    Pull network devices from UniFi and create/update local device records.
    """
    unifi_devices = fetch_devices_from_unifi()
    created = 0
    updated = 0
    errors = []

    # Ensure we have a device type for UniFi devices
    for type_name in ["Gateway", "Switch", "Access Point"]:
        existing_type = session.query(DeviceType).filter(DeviceType.name == type_name).first()
        if not existing_type:
            session.add(DeviceType(name=type_name))
    session.flush()

    type_map = {dt.name.lower(): dt.id for dt in session.query(DeviceType).all()}

    for udev in unifi_devices:
        try:
            name = udev.get("name") or udev.get("hostname") or udev.get("mac", "Unknown")
            mac = (udev.get("mac") or udev.get("macAddress") or "").upper().replace("-", ":")
            model = udev.get("model")
            dev_type = (udev.get("type") or "").lower()
            features = udev.get("features", [])

            # Map UniFi device type to our types
            is_gateway = (
                "gw" in dev_type or "gateway" in dev_type
                or "dream machine" in (model or "").lower()
                or "udm" in (model or "").lower()
            )
            is_ap = (
                "ap" in dev_type or "access point" in dev_type
                or "accessPoint" in features
            )
            is_switch = (
                "sw" in dev_type or "switch" in dev_type
                or "switching" in features
            )

            if is_gateway:
                device_type_id = type_map.get("gateway")
            elif is_ap:
                device_type_id = type_map.get("access point")
            elif is_switch:
                device_type_id = type_map.get("switch")
            else:
                device_type_id = type_map.get("other")

            # Find existing by MAC address (normalized) or by name
            existing = None
            if mac:
                # Normalize: search for MAC with or without colons
                mac_normalized = mac.replace(":", "").replace("-", "").upper()
                all_devices = session.query(Device).filter(Device.mac_address.isnot(None)).all()
                for d in all_devices:
                    d_mac = (d.mac_address or "").replace(":", "").replace("-", "").upper()
                    if d_mac == mac_normalized:
                        existing = d
                        break
            if not existing:
                # Fall back to name match
                existing = session.query(Device).filter(Device.name == name).first()

            if existing:
                changed = False
                if existing.name != name:
                    existing.name = name
                    changed = True
                if model and existing.model != model:
                    existing.model = model
                    changed = True
                if mac and not existing.mac_address:
                    existing.mac_address = mac
                    changed = True
                if changed:
                    updated += 1
                device_record = existing
            else:
                new_dev = Device(
                    name=name,
                    mac_address=mac or None,
                    manufacturer="Ubiquiti",
                    model=model,
                    device_type_id=device_type_id,
                    notes=f"UniFi device ID: {udev.get('id', '')}",
                )
                session.add(new_dev)
                session.flush()
                log_change(
                    session,
                    entity_type=EntityType.DEVICE,
                    entity_id=new_dev.id,
                    action=ActionType.CREATED,
                    entity_name=name,
                    new_values={"mac": mac, "model": model, "source": "unifi_sync"},
                    comment="Imported from UniFi controller",
                )
                created += 1
                device_record = new_dev

            # Create/update IP address for this device
            dev_ip = udev.get("ipAddress")
            if dev_ip and device_record:
                import ipaddress as _ipa
                # Find matching network
                target_net = None
                for net in session.query(Network).all():
                    try:
                        if _ipa.ip_address(dev_ip) in _ipa.ip_network(net.cidr, strict=False):
                            target_net = net
                            break
                    except ValueError:
                        continue

                # If IP doesn't match any network (e.g. WAN IP on gateway), use gateway IP instead
                if not target_net and is_gateway:
                    # This is likely the gateway device - assign its LAN IP
                    for net in session.query(Network).all():
                        if net.gateway:
                            dev_ip = net.gateway
                            target_net = net
                            break
                    # If no gateway stored, use the first network's .254
                    if not target_net:
                        first_net = session.query(Network).first()
                        if first_net:
                            try:
                                net_obj = _ipa.ip_network(first_net.cidr, strict=False)
                                # Use last usable host as gateway IP
                                hosts = list(net_obj.hosts())
                                dev_ip = str(hosts[-1]) if hosts else None
                                target_net = first_net
                            except ValueError:
                                pass

                if target_net:
                    existing_ip = session.query(IPAddress).filter(IPAddress.address == dev_ip).first()
                    if existing_ip:
                        # Link device if not linked
                        if existing_ip.device_id != device_record.id:
                            existing_ip.device_id = device_record.id
                        existing_ip.status = IPStatus.ACTIVE
                        existing_ip.assignment_type = AssignmentType.STATIC
                        existing_ip.last_seen = datetime.now(timezone.utc)
                        if not existing_ip.hostname:
                            existing_ip.hostname = name
                    else:
                        new_ip = IPAddress(
                            address=dev_ip,
                            network_id=target_net.id,
                            device_id=device_record.id,
                            hostname=name,
                            mac_address=mac or None,
                            assignment_type=AssignmentType.STATIC,
                            status=IPStatus.ACTIVE,
                            last_seen=datetime.now(timezone.utc),
                            source="unifi_device",
                        )
                        session.add(new_ip)

        except Exception as e:
            errors.append(f"Device '{udev.get('name', '?')}': {e}")

    session.commit()
    return {"created": created, "updated": updated, "errors": errors}


def sync_clients(session: Session) -> dict:
    """
    Pull active clients from UniFi and create/update IP address records.
    """
    unifi_clients = fetch_clients_from_unifi()
    created = 0
    updated = 0
    skipped = 0
    errors = []

    # Pre-load networks for matching
    import ipaddress as ipaddress_mod
    networks = session.query(Network).all()
    network_cidrs = []
    for net in networks:
        try:
            network_cidrs.append((net, ipaddress_mod.ip_network(net.cidr, strict=False)))
        except ValueError:
            pass

    # Fetch DHCP ranges from UniFi to determine static vs DHCP
    dhcp_ranges: list[tuple[ipaddress_mod.IPv4Address, ipaddress_mod.IPv4Address]] = []
    try:
        unifi_networks = fetch_networks_from_unifi()
        for unet in unifi_networks:
            ipv4_config = unet.get("ipv4Configuration")
            if isinstance(ipv4_config, dict):
                dhcp_config = ipv4_config.get("dhcpConfiguration")
                if isinstance(dhcp_config, dict):
                    ip_range = dhcp_config.get("ipAddressRange")
                    if isinstance(ip_range, dict) and ip_range.get("start") and ip_range.get("stop"):
                        try:
                            start = ipaddress_mod.ip_address(ip_range["start"])
                            stop = ipaddress_mod.ip_address(ip_range["stop"])
                            dhcp_ranges.append((start, stop))
                        except ValueError:
                            pass
    except Exception:
        pass  # If we can't get DHCP ranges, default to DHCP

    def is_in_dhcp_range(ip_str: str) -> bool:
        """Check if an IP falls within any known DHCP range."""
        try:
            ip_obj = ipaddress_mod.ip_address(ip_str)
            for start, stop in dhcp_ranges:
                if start <= ip_obj <= stop:
                    return True
        except ValueError:
            pass
        return False

    skipped_ips = []

    for client in unifi_clients:
        try:
            ip_addr = (
                client.get("ip")
                or client.get("ipAddress")
                or client.get("fixedIp")
                or client.get("fixed_ip")
            )
            if not ip_addr:
                skipped += 1
                continue

            mac = (client.get("mac") or client.get("macAddress") or "").upper().replace("-", ":")
            hostname = client.get("name") or client.get("hostname")
            is_fixed = client.get("useFixedIp", False) or client.get("use_fixed_ip", False)

            # Determine assignment type: if IP is outside DHCP range, it's static
            if is_fixed or (dhcp_ranges and not is_in_dhcp_range(ip_addr)):
                assignment = AssignmentType.STATIC
            else:
                assignment = AssignmentType.DHCP

            # Find which network this IP belongs to
            target_network = None
            try:
                ip_obj = ipaddress_mod.ip_address(ip_addr)
                for net, net_obj in network_cidrs:
                    if ip_obj in net_obj:
                        target_network = net
                        break
            except ValueError:
                skipped += 1
                errors.append(f"Invalid IP: {ip_addr}")
                continue

            if not target_network:
                skipped += 1
                skipped_ips.append(ip_addr)
                continue

            # Check if IP already exists
            existing = session.query(IPAddress).filter(IPAddress.address == ip_addr).first()

            if existing:
                changed = False
                if hostname and existing.hostname != hostname:
                    existing.hostname = hostname
                    changed = True
                if mac and existing.mac_address != mac:
                    existing.mac_address = mac
                    changed = True
                if existing.assignment_type != assignment:
                    existing.assignment_type = assignment
                    changed = True
                existing.last_seen = datetime.now(timezone.utc)
                existing.status = IPStatus.ACTIVE
                if changed:
                    updated += 1
            else:
                new_ip = IPAddress(
                    address=ip_addr,
                    network_id=target_network.id,
                    hostname=hostname,
                    mac_address=mac or None,
                    assignment_type=assignment,
                    status=IPStatus.ACTIVE,
                    last_seen=datetime.now(timezone.utc),
                    source="unifi_client",
                )
                session.add(new_ip)
                session.flush()
                log_change(
                    session,
                    entity_type=EntityType.IP_ADDRESS,
                    entity_id=new_ip.id,
                    action=ActionType.CREATED,
                    entity_name=ip_addr,
                    new_values={"address": ip_addr, "hostname": hostname, "source": "unifi_sync"},
                    comment="Imported from UniFi client list",
                )
                created += 1
        except Exception as e:
            errors.append(f"Client '{client.get('name', client.get('mac', '?'))}': {e}")

    session.commit()

    # Add skipped IPs info to errors for visibility
    if skipped_ips:
        missing_subnets = set()
        for ip in skipped_ips:
            parts = ip.split(".")
            if len(parts) == 4:
                missing_subnets.add(f"{parts[0]}.{parts[1]}.{parts[2]}.0/24")
        errors.append(
            f"Skipped {len(skipped_ips)} IPs with no matching local network. "
            f"Missing subnets: {', '.join(sorted(missing_subnets))}. "
            f"Sample IPs: {', '.join(skipped_ips[:8])}"
        )

    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}


def test_connection() -> dict:
    """Test the UniFi API connection. Returns status info."""
    if not is_configured():
        return {"success": False, "error": "UniFi integration not configured. Set UNIFI_API_KEY, UNIFI_BASE_URL, and UNIFI_SITE_ID in .env"}

    try:
        sites = fetch_sites()
        return {
            "success": True,
            "sites": len(sites),
            "site_names": [s.get("name", "?") for s in sites],
        }
    except httpx.ConnectError:
        return {"success": False, "error": f"Cannot connect to {UNIFI_BASE_URL}"}
    except httpx.HTTPStatusError as e:
        return {"success": False, "error": f"HTTP {e.response.status_code}: Check API key"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_raw_networks() -> list[dict]:
    """Fetch raw network data from UniFi for debugging field names."""
    return fetch_networks_from_unifi()


def fetch_raw_clients() -> list[dict]:
    """Fetch raw client data from UniFi for debugging field names."""
    return fetch_clients_from_unifi()
