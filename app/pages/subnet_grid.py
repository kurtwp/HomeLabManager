"""Visual subnet grid component — shows IP allocation as a color-coded grid."""

import ipaddress
from nicegui import ui

from app.models.ip_address import IPAddress, AssignmentType, IPStatus


def render_subnet_grid(network_cidr: str, ip_addresses: list[IPAddress]):
    """
    Render a visual grid showing all IPs in a subnet.
    Each cell is color-coded by assignment type and status.
    """
    net = ipaddress.ip_network(network_cidr, strict=False)
    all_hosts = list(net.hosts())

    # Build lookup of tracked IPs
    ip_lookup: dict[str, IPAddress] = {ip.address: ip for ip in ip_addresses}

    # Determine grid sizing
    total = len(all_hosts)
    if total <= 256:
        cols = 16
    elif total <= 512:
        cols = 32
    else:
        # For large subnets, only show first 256 hosts with a note
        all_hosts = all_hosts[:256]
        cols = 16

    # Legend
    with ui.row().classes("gap-4 mb-3 flex-wrap"):
        _legend_item("Free", "#e8f5e9", "#c8e6c9")
        _legend_item("Static", "#1976d2", "#1565c0")
        _legend_item("DHCP", "#ff9800", "#f57c00")
        _legend_item("Reserved", "#9e9e9e", "#757575")
        _legend_item("Inactive", "#ffcdd2", "#ef9a9a")

    if total > 256:
        ui.label(
            f"Showing first 256 of {total} hosts. Use the table below for full list."
        ).classes("text-xs text-gray-500 mb-2")

    # Grid container
    grid_html = _build_grid_html(all_hosts, ip_lookup, cols)
    ui.html(grid_html)


def _build_grid_html(
    hosts: list[ipaddress.IPv4Address | ipaddress.IPv6Address],
    ip_lookup: dict[str, IPAddress],
    cols: int,
) -> str:
    """Build the HTML for the subnet grid."""
    cells = []
    for host in hosts:
        host_str = str(host)
        ip_entry = ip_lookup.get(host_str)

        if ip_entry:
            if ip_entry.status == IPStatus.INACTIVE:
                bg = "#ffcdd2"
                border = "#ef9a9a"
                color = "#b71c1c"
            elif ip_entry.assignment_type == AssignmentType.STATIC:
                bg = "#1976d2"
                border = "#1565c0"
                color = "white"
            elif ip_entry.assignment_type == AssignmentType.RESERVED:
                bg = "#9e9e9e"
                border = "#757575"
                color = "white"
            else:  # DHCP
                bg = "#ff9800"
                border = "#f57c00"
                color = "white"
            tooltip = f"{host_str}"
            if ip_entry.hostname:
                tooltip += f" ({ip_entry.hostname})"
            tooltip += f" [{ip_entry.assignment_type.value}]"
        else:
            bg = "#e8f5e9"
            border = "#c8e6c9"
            color = "#388e3c"
            tooltip = f"{host_str} (free)"

        # Get last octet for display
        last_octet = str(host).split(".")[-1] if "." in str(host) else str(host)[-4:]

        cells.append(
            f'<div class="ip-cell" '
            f'style="background-color:{bg}; border:1px solid {border}; color:{color};" '
            f'title="{tooltip}">'
            f'{last_octet}</div>'
        )

    grid_style = (
        f"display:grid; grid-template-columns:repeat({cols}, 1fr); "
        f"gap:2px; padding:8px;"
    )
    return (
        f'<div style="{grid_style}">'
        + "".join(cells)
        + "</div>"
        + """
        <style>
        .ip-cell {
            aspect-ratio: 1;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.6rem;
            cursor: pointer;
            transition: transform 0.15s ease;
            font-weight: 500;
        }
        .ip-cell:hover {
            transform: scale(1.3);
            z-index: 10;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }
        </style>
        """
    )


def _legend_item(label: str, bg: str, border: str):
    """Render a legend color swatch + label."""
    ui.html(
        f'<div style="display:inline-flex; align-items:center; gap:4px;">'
        f'<div style="width:14px; height:14px; border-radius:3px; '
        f'background:{bg}; border:1px solid {border};"></div>'
        f'<span style="font-size:0.75rem;">{label}</span></div>'
    )
