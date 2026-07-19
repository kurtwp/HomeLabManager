"""Inventory Export page — generate Ansible/Terraform inventory files."""

import io
from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.models.device import Device, DeviceType
from app.models.ip_address import IPAddress, IPStatus
from app.models.network import Network
from app.pages.layout import page_layout


def render_inventory_export():
    """Render the inventory export page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Inventory Export").classes("text-3xl font-bold")
        ui.label(
            "Generate Ansible or Terraform inventory files from your device and IP data."
        ).classes("text-gray-500 mb-4")

        ui.separator()

        # Options
        with ui.card().classes("w-full mt-4"):
            ui.label("Export Options").classes("text-lg font-semibold mb-2")

            with ui.row().classes("gap-4 items-end flex-wrap"):
                format_select = ui.select(
                    {
                        "ansible_ini": "Ansible INI",
                        "ansible_yaml": "Ansible YAML",
                        "terraform_hosts": "Terraform (local-exec hosts)",
                        "terraform_vars": "Terraform Variables (tfvars)",
                    },
                    value="ansible_ini",
                    label="Format",
                ).classes("w-64")

                source_select = ui.select(
                    {"devices": "Devices (grouped by type)", "ips_active": "Active IPs (grouped by network)"},
                    value="devices",
                    label="Data Source",
                ).classes("w-64")

                only_with_ip = ui.switch("Only devices with IPs", value=True)

        # Preview + Download
        with ui.card().classes("w-full mt-4"):
            ui.label("Preview").classes("text-lg font-semibold mb-2")

            preview_container = ui.column().classes("w-full")

            def generate_and_preview():
                preview_container.clear()
                fmt = format_select.value
                source = source_select.value

                if source == "devices":
                    content = _generate_from_devices(session, fmt, only_with_ip.value)
                else:
                    content = _generate_from_ips(session, fmt)

                with preview_container:
                    ui.code(content, language="yaml" if "yaml" in fmt else "ini").classes(
                        "w-full text-xs"
                    ).style("max-height: 400px; overflow-y: auto;")

                    def do_download():
                        ext = {"ansible_ini": "ini", "ansible_yaml": "yml",
                               "terraform_hosts": "tf", "terraform_vars": "tfvars"}.get(fmt, "txt")
                        filename = f"inventory.{ext}"
                        ui.download(content.encode("utf-8"), filename, "text/plain")
                        ui.notify(f"Downloaded {filename}", type="positive")

                    with ui.row().classes("gap-2 mt-3"):
                        ui.button("Download", icon="download", on_click=do_download).props(
                            "color=primary"
                        )
                        ui.button("Copy to Clipboard", icon="content_copy",
                                  on_click=lambda: (ui.clipboard.write(content),
                                                    ui.notify("Copied!", type="positive"))).props(
                            "color=blue outline"
                        )

            ui.button("Generate", icon="code", on_click=generate_and_preview).props(
                "color=primary"
            ).classes("mb-3")

    session.close()


def _generate_from_devices(session, fmt: str, only_with_ip: bool) -> str:
    """Generate inventory from devices grouped by device type."""
    devices = session.query(Device).order_by(Device.name).all()

    # Group by type
    groups: dict[str, list[dict]] = {}
    for dev in devices:
        ips = [ip.address for ip in dev.ip_addresses if ip.status == IPStatus.ACTIVE]
        if only_with_ip and not ips:
            continue
        group_name = dev.device_type.name.lower().replace(" ", "_") if dev.device_type else "ungrouped"
        if group_name not in groups:
            groups[group_name] = []
        groups[group_name].append({
            "name": _sanitize_hostname(dev.name),
            "ip": ips[0] if ips else dev.name,
            "ips": ips,
            "mac": dev.mac_address or "",
            "manufacturer": dev.manufacturer or "",
            "model": dev.model or "",
        })

    if fmt == "ansible_ini":
        return _to_ansible_ini(groups)
    elif fmt == "ansible_yaml":
        return _to_ansible_yaml(groups)
    elif fmt == "terraform_hosts":
        return _to_terraform_hosts(groups)
    elif fmt == "terraform_vars":
        return _to_terraform_vars(groups)
    return "# Unknown format"


def _generate_from_ips(session, fmt: str) -> str:
    """Generate inventory from active IPs grouped by network."""
    networks = session.query(Network).order_by(Network.name).all()

    groups: dict[str, list[dict]] = {}
    for net in networks:
        active_ips = [ip for ip in net.ip_addresses if ip.status == IPStatus.ACTIVE]
        if not active_ips:
            continue
        group_name = _sanitize_hostname(net.name)
        groups[group_name] = []
        for ip in sorted(active_ips, key=lambda x: x.address):
            groups[group_name].append({
                "name": _sanitize_hostname(ip.hostname or ip.address),
                "ip": ip.address,
                "ips": [ip.address],
                "mac": ip.mac_address or "",
                "manufacturer": "",
                "model": "",
            })

    if fmt == "ansible_ini":
        return _to_ansible_ini(groups)
    elif fmt == "ansible_yaml":
        return _to_ansible_yaml(groups)
    elif fmt == "terraform_hosts":
        return _to_terraform_hosts(groups)
    elif fmt == "terraform_vars":
        return _to_terraform_vars(groups)
    return "# Unknown format"


def _sanitize_hostname(name: str) -> str:
    """Make a string safe for use as a hostname/group name."""
    import re
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_\-]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_") or "host"


def _to_ansible_ini(groups: dict[str, list[dict]]) -> str:
    """Generate Ansible INI inventory."""
    lines = ["# Ansible Inventory — generated by Home Lab Manager", ""]
    for group, hosts in sorted(groups.items()):
        lines.append(f"[{group}]")
        for host in hosts:
            extra = ""
            if host["mac"]:
                extra += f" mac={host['mac']}"
            lines.append(f"{host['ip']}  # {host['name']}{extra}")
        lines.append("")
    return "\n".join(lines)


def _to_ansible_yaml(groups: dict[str, list[dict]]) -> str:
    """Generate Ansible YAML inventory."""
    lines = ["# Ansible Inventory — generated by Home Lab Manager", "all:", "  children:"]
    for group, hosts in sorted(groups.items()):
        lines.append(f"    {group}:")
        lines.append(f"      hosts:")
        for host in hosts:
            lines.append(f"        {host['name']}:")
            lines.append(f"          ansible_host: {host['ip']}")
            if host["mac"]:
                lines.append(f"          mac_address: {host['mac']}")
            if host["manufacturer"]:
                lines.append(f"          manufacturer: {host['manufacturer']}")
    return "\n".join(lines)


def _to_terraform_hosts(groups: dict[str, list[dict]]) -> str:
    """Generate Terraform locals block with host lists."""
    lines = ['# Terraform Hosts — generated by Home Lab Manager', '',
             'locals {']
    for group, hosts in sorted(groups.items()):
        ips = [h["ip"] for h in hosts]
        lines.append(f'  {group}_hosts = [')
        for ip in ips:
            lines.append(f'    "{ip}",')
        lines.append('  ]')
        lines.append('')
    lines.append('}')
    return "\n".join(lines)


def _to_terraform_vars(groups: dict[str, list[dict]]) -> str:
    """Generate Terraform .tfvars file."""
    lines = ['# Terraform Variables — generated by Home Lab Manager', '']
    for group, hosts in sorted(groups.items()):
        lines.append(f'{group}_hosts = [')
        for host in hosts:
            lines.append(f'  "{host["ip"]}",  # {host["name"]}')
        lines.append(']')
        lines.append('')
    return "\n".join(lines)
