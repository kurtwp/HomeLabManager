"""Nmap manual scan page — run nmap commands and view results."""

import subprocess
import re
from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.network_service import get_all_networks
from app.pages.layout import page_layout


def render_nmap():
    """Render the Nmap manual scan page."""
    page_layout()

    session = get_session()

    with ui.column().classes("page-container w-full"):
        ui.label("Nmap Scanner").classes("text-3xl font-bold")
        ui.label("Run nmap commands and view results directly.").classes(
            "text-gray-500 mb-4"
        )

        ui.separator()

        with ui.tabs().classes("w-full") as tabs:
            quick_tab = ui.tab("Quick Scan")
            custom_tab = ui.tab("Custom Command")

        with ui.tab_panels(tabs, value=quick_tab).classes("w-full"):
            # --- Quick Scan Presets ---
            with ui.tab_panel(quick_tab):
                with ui.card().classes("w-full"):
                    ui.label("Quick Scan").classes("text-xl font-semibold mb-2")
                    ui.label("Select a target and scan type.").classes(
                        "text-sm text-gray-500 mb-4"
                    )

                    networks = get_all_networks(session)
                    target_options = {n.cidr: f"{n.name} ({n.cidr})" for n in networks}

                    with ui.row().classes("gap-4 items-end flex-wrap"):
                        target_input = ui.input(
                            "Target (IP, range, or CIDR)",
                            placeholder="192.168.2.0/24 or 192.168.2.1-50",
                        ).classes("w-72")

                        # Quick fill from known networks
                        if target_options:
                            net_select = ui.select(
                                target_options, label="Or pick a network"
                            ).classes("w-64")
                            net_select.on(
                                "update:model-value",
                                lambda: setattr(target_input, 'value', net_select.value) if net_select.value else None,
                            )

                    scan_type = ui.select(
                        {
                            "-sn": "Ping Scan (host discovery only)",
                            "-sS": "SYN Scan (stealth port scan)",
                            "-sT": "TCP Connect Scan (full connect)",
                            "-sV": "Service Version Detection",
                            "-sV -O": "Service + OS Detection",
                            "-A": "Aggressive (OS, version, scripts, traceroute)",
                            "-p 1-1024": "Common Ports (1-1024)",
                            "-p-": "All Ports (1-65535, slow)",
                        },
                        value="-sn",
                        label="Scan Type",
                    ).classes("w-full mt-2")

                    # Additional options
                    with ui.row().classes("gap-4 mt-2"):
                        timing_select = ui.select(
                            {"": "Default", "-T2": "Slow (T2)", "-T3": "Normal (T3)", "-T4": "Fast (T4)", "-T5": "Insane (T5)"},
                            value="-T4",
                            label="Timing",
                        ).classes("w-40")
                        extra_args = ui.input(
                            "Extra Arguments", placeholder="e.g. --top-ports 100"
                        ).classes("w-64")

                    quick_results = ui.column().classes("w-full mt-4")

                    def run_quick_scan():
                        target = target_input.value
                        if not target:
                            ui.notify("Enter a target", type="warning")
                            return

                        # Build command
                        cmd_parts = ["nmap"]
                        if scan_type.value:
                            cmd_parts.extend(scan_type.value.split())
                        if timing_select.value:
                            cmd_parts.append(timing_select.value)
                        if extra_args.value:
                            cmd_parts.extend(extra_args.value.split())
                        cmd_parts.append(target)

                        cmd_str = " ".join(cmd_parts)

                        quick_results.clear()
                        with quick_results:
                            with ui.row().classes("items-center gap-3"):
                                ui.spinner(size="lg")
                                ui.label(f"Running: {cmd_str}").classes(
                                    "text-sm font-mono text-gray-500"
                                )

                        _execute_nmap(cmd_parts, cmd_str, quick_results)

                    ui.button(
                        "Run Scan", icon="radar", on_click=run_quick_scan
                    ).props("color=primary").classes("mt-3")

            # --- Custom Command ---
            with ui.tab_panel(custom_tab):
                with ui.card().classes("w-full"):
                    ui.label("Custom Nmap Command").classes("text-xl font-semibold mb-2")
                    ui.label(
                        "Enter any nmap command. The 'nmap' prefix is added automatically."
                    ).classes("text-sm text-gray-500 mb-4")

                    cmd_input = ui.input(
                        "Nmap Arguments",
                        placeholder="e.g. -sV -T4 192.168.2.0/24",
                    ).classes("w-full").props('outlined')

                    ui.label("Examples:").classes("text-xs text-gray-400 mt-2")
                    with ui.column().classes("gap-0 ml-4"):
                        examples = [
                            "-sn 192.168.2.0/24",
                            "-sV -p 22,80,443 192.168.2.5",
                            "-A -T4 192.168.2.1",
                            "-sU -p 161 192.168.2.0/24",
                            "--top-ports 20 192.168.2.0/24",
                        ]
                        for ex in examples:
                            ui.label(f"nmap {ex}").classes(
                                "text-xs font-mono text-gray-500 cursor-pointer"
                            ).on("click", lambda e=ex: setattr(cmd_input, 'value', e))

                    custom_results = ui.column().classes("w-full mt-4")

                    def run_custom_scan():
                        if not cmd_input.value:
                            ui.notify("Enter nmap arguments", type="warning")
                            return

                        cmd_parts = ["nmap"] + cmd_input.value.split()
                        cmd_str = " ".join(cmd_parts)

                        custom_results.clear()
                        with custom_results:
                            with ui.row().classes("items-center gap-3"):
                                ui.spinner(size="lg")
                                ui.label(f"Running: {cmd_str}").classes(
                                    "text-sm font-mono text-gray-500"
                                )

                        _execute_nmap(cmd_parts, cmd_str, custom_results)

                    ui.button(
                        "Run Command", icon="terminal", on_click=run_custom_scan
                    ).props("color=primary").classes("mt-3")

    session.close()


def _execute_nmap(cmd_parts: list[str], cmd_str: str, results_container):
    """Execute an nmap command and render results."""
    try:
        result = subprocess.run(
            cmd_parts,
            capture_output=True, text=True, timeout=300,  # 5 min max
        )

        results_container.clear()
        with results_container:
            # Show command that was run
            with ui.card().classes("w-full"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("terminal").classes("text-gray-500")
                    ui.label(cmd_str).classes("font-mono text-sm")

            if result.returncode != 0 and result.stderr:
                with ui.card().classes("w-full bg-red-50 dark:bg-red-900 mt-2"):
                    ui.label("Error").classes("font-semibold text-red")
                    ui.code(result.stderr, language="text").classes("w-full text-xs")

            if result.stdout:
                # Parse and display results
                output = result.stdout

                # Extract summary stats
                hosts_up = len(re.findall(r"Host is up", output))
                ports_open = len(re.findall(r"(\d+)/\w+\s+open", output))

                with ui.row().classes("gap-4 mt-2 mb-2"):
                    if hosts_up:
                        ui.badge(f"{hosts_up} hosts up").props("color=green")
                    if ports_open:
                        ui.badge(f"{ports_open} open ports").props("color=blue")

                # Structured output — parse host blocks
                host_blocks = _parse_nmap_output(output)

                if host_blocks:
                    for host in host_blocks:
                        with ui.expansion(
                            f"{host['ip']} — {host.get('hostname', '')}",
                            icon="computer",
                        ).classes("w-full"):
                            if host.get("state"):
                                ui.label(f"State: {host['state']}").classes("text-sm")
                            if host.get("latency"):
                                ui.label(f"Latency: {host['latency']}").classes("text-sm text-gray-500")
                            if host.get("os"):
                                ui.label(f"OS: {host['os']}").classes("text-sm")
                            if host.get("ports"):
                                columns = [
                                    {"name": "port", "label": "Port", "field": "port", "align": "left"},
                                    {"name": "state", "label": "State", "field": "state", "align": "center"},
                                    {"name": "service", "label": "Service", "field": "service", "align": "left"},
                                    {"name": "version", "label": "Version", "field": "version", "align": "left"},
                                ]
                                ui.table(
                                    columns=columns, rows=host["ports"], row_key="port"
                                ).classes("w-full").props("flat bordered dense")

                # Always show raw output in expandable section
                with ui.expansion("Raw Output", icon="code").classes("w-full mt-2"):
                    ui.code(output, language="text").classes("w-full text-xs")
            else:
                ui.label("No output returned.").classes("text-gray-500 mt-2")

    except subprocess.TimeoutExpired:
        results_container.clear()
        with results_container:
            ui.label("⚠️ Scan timed out (5 minute limit).").classes("text-orange")
    except FileNotFoundError:
        results_container.clear()
        with results_container:
            ui.label("❌ nmap not found. Install with: sudo apt install nmap").classes("text-red")
    except Exception as e:
        results_container.clear()
        with results_container:
            ui.label(f"❌ Error: {e}").classes("text-red")


def _parse_nmap_output(output: str) -> list[dict]:
    """Parse nmap output into structured host data."""
    hosts = []
    current_host = None

    for line in output.split("\n"):
        # New host block
        match = re.match(r"Nmap scan report for (?:(.+?) )?\(?(\d+\.\d+\.\d+\.\d+)\)?", line)
        if match:
            if current_host:
                hosts.append(current_host)
            hostname = match.group(1) or ""
            ip = match.group(2)
            current_host = {"ip": ip, "hostname": hostname.strip(), "ports": []}
            continue

        if not current_host:
            continue

        # Host state
        if "Host is up" in line:
            current_host["state"] = "up"
            latency_match = re.search(r"\(([\d.]+)s latency\)", line)
            if latency_match:
                current_host["latency"] = latency_match.group(1) + "s"

        # Port line: "22/tcp  open  ssh  OpenSSH 8.9p1"
        port_match = re.match(r"\s*(\d+/\w+)\s+(open|closed|filtered)\s+(\S+)\s*(.*)", line)
        if port_match:
            current_host["ports"].append({
                "port": port_match.group(1),
                "state": port_match.group(2),
                "service": port_match.group(3),
                "version": port_match.group(4).strip(),
            })

        # OS detection
        if "OS details:" in line:
            current_host["os"] = line.split("OS details:", 1)[1].strip()
        elif "Running:" in line:
            current_host["os"] = line.split("Running:", 1)[1].strip()

    if current_host:
        hosts.append(current_host)

    return hosts
