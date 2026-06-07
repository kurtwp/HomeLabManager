"""IPv4/IPv6 subnet calculator page."""

import ipaddress

from nicegui import ui

from app.pages.layout import page_layout


def render_calculator():
    """Render the subnet calculator page."""
    page_layout()

    with ui.column().classes("page-container w-full"):
        ui.label("IP Calculator").classes("text-3xl font-bold")
        ui.separator().classes("my-4")

        with ui.tabs().classes("w-full") as tabs:
            calc_tab = ui.tab("Subnet Calculator")
            split_tab = ui.tab("Subnet Splitter")
            check_tab = ui.tab("IP-in-Subnet Check")

        with ui.tab_panels(tabs, value=calc_tab).classes("w-full"):
            # --- Subnet Calculator ---
            with ui.tab_panel(calc_tab):
                with ui.card().classes("w-full"):
                    ui.label("Subnet Calculator").classes("text-xl font-semibold mb-2")
                    ui.label("Enter a CIDR notation to calculate subnet details.").classes(
                        "text-sm text-gray-500 mb-4"
                    )

                    cidr_input = ui.input(
                        "CIDR Notation",
                        placeholder="e.g. 192.168.1.0/24 or 2001:db8::/32",
                    ).classes("w-96")

                    calc_results = ui.column().classes("w-full mt-4")

                    def calculate_subnet():
                        calc_results.clear()
                        with calc_results:
                            try:
                                network = ipaddress.ip_network(cidr_input.value, strict=False)
                            except (ValueError, TypeError) as e:
                                ui.label(f"Invalid CIDR: {e}").classes("text-red")
                                return

                            is_v6 = isinstance(network, ipaddress.IPv6Network)

                            with ui.card().classes("w-full bg-blue-50 dark:bg-gray-800"):
                                ui.label("Results").classes("text-lg font-semibold mb-2")

                                data = [
                                    ("Network Address", str(network.network_address)),
                                    ("Broadcast Address", str(network.broadcast_address) if not is_v6 else "N/A (IPv6)"),
                                    ("Netmask", str(network.netmask)),
                                    ("Host Mask", str(network.hostmask)),
                                    ("Prefix Length", f"/{network.prefixlen}"),
                                    ("Total Addresses", f"{network.num_addresses:,}"),
                                ]

                                if not is_v6:
                                    hosts = list(network.hosts())
                                    if hosts:
                                        data.append(("First Host", str(hosts[0])))
                                        data.append(("Last Host", str(hosts[-1])))
                                        data.append(("Usable Hosts", f"{len(hosts):,}"))
                                    else:
                                        data.append(("Usable Hosts", "0 (point-to-point or host)"))
                                else:
                                    # For IPv6, don't enumerate all hosts
                                    total = network.num_addresses
                                    if total > 2:
                                        first_host = network.network_address + 1
                                        last_host = network.broadcast_address - 1
                                        data.append(("First Host", str(first_host)))
                                        data.append(("Last Host", str(last_host)))
                                        data.append(("Usable Hosts", f"{total - 2:,}"))

                                # Network class (IPv4 only)
                                if not is_v6:
                                    first_octet = int(str(network.network_address).split(".")[0])
                                    if first_octet < 128:
                                        net_class = "A"
                                    elif first_octet < 192:
                                        net_class = "B"
                                    elif first_octet < 224:
                                        net_class = "C"
                                    elif first_octet < 240:
                                        net_class = "D (Multicast)"
                                    else:
                                        net_class = "E (Reserved)"
                                    data.append(("Network Class", net_class))
                                    data.append(("Private", "Yes" if network.is_private else "No"))

                                columns = [
                                    {"name": "property", "label": "Property", "field": "property", "align": "left"},
                                    {"name": "value", "label": "Value", "field": "value", "align": "left"},
                                ]
                                rows = [{"property": k, "value": v} for k, v in data]
                                ui.table(columns=columns, rows=rows, row_key="property").classes(
                                    "w-full"
                                ).props("flat dense hide-header")

                    ui.button("Calculate", on_click=calculate_subnet).props(
                        "color=primary icon=calculate"
                    ).classes("mt-2")

            # --- Subnet Splitter ---
            with ui.tab_panel(split_tab):
                with ui.card().classes("w-full"):
                    ui.label("Subnet Splitter").classes("text-xl font-semibold mb-2")
                    ui.label(
                        "Split a network into smaller subnets by specifying the new prefix length."
                    ).classes("text-sm text-gray-500 mb-4")

                    with ui.row().classes("gap-4 items-end"):
                        split_cidr_input = ui.input(
                            "Network CIDR",
                            placeholder="e.g. 192.168.1.0/24",
                        ).classes("w-64")
                        split_prefix_input = ui.number(
                            "New Prefix Length",
                            value=26,
                            min=1,
                            max=128,
                        ).classes("w-48")

                    split_results = ui.column().classes("w-full mt-4")

                    def split_subnet():
                        split_results.clear()
                        with split_results:
                            try:
                                network = ipaddress.ip_network(split_cidr_input.value, strict=False)
                            except (ValueError, TypeError) as e:
                                ui.label(f"Invalid CIDR: {e}").classes("text-red")
                                return

                            new_prefix = int(split_prefix_input.value)
                            if new_prefix <= network.prefixlen:
                                ui.label(
                                    f"New prefix (/{new_prefix}) must be larger than current (/{network.prefixlen})"
                                ).classes("text-red")
                                return

                            try:
                                subnets = list(network.subnets(new_prefix=new_prefix))
                            except ValueError as e:
                                ui.label(f"Error: {e}").classes("text-red")
                                return

                            if len(subnets) > 256:
                                ui.label(
                                    f"Too many subnets ({len(subnets)}). Showing first 256."
                                ).classes("text-orange mb-2")
                                subnets = subnets[:256]

                            ui.label(f"Split into {len(subnets)} subnets:").classes(
                                "text-lg font-semibold mb-2"
                            )

                            columns = [
                                {"name": "subnet", "label": "Subnet", "field": "subnet", "align": "left"},
                                {"name": "first", "label": "First Host", "field": "first", "align": "left"},
                                {"name": "last", "label": "Last Host", "field": "last", "align": "left"},
                                {"name": "hosts", "label": "Usable Hosts", "field": "hosts", "align": "right"},
                            ]
                            rows = []
                            for subnet in subnets:
                                hosts = list(subnet.hosts())
                                rows.append({
                                    "subnet": str(subnet),
                                    "first": str(hosts[0]) if hosts else "—",
                                    "last": str(hosts[-1]) if hosts else "—",
                                    "hosts": len(hosts),
                                })

                            ui.table(columns=columns, rows=rows, row_key="subnet").classes(
                                "w-full"
                            ).props("flat bordered dense")

                    ui.button("Split", on_click=split_subnet).props(
                        "color=primary icon=call_split"
                    ).classes("mt-2")

            # --- IP in Subnet Check ---
            with ui.tab_panel(check_tab):
                with ui.card().classes("w-full"):
                    ui.label("IP-in-Subnet Checker").classes("text-xl font-semibold mb-2")
                    ui.label("Check if an IP address belongs to a given subnet.").classes(
                        "text-sm text-gray-500 mb-4"
                    )

                    with ui.row().classes("gap-4 items-end"):
                        check_ip_input = ui.input(
                            "IP Address",
                            placeholder="e.g. 192.168.1.50",
                        ).classes("w-64")
                        check_subnet_input = ui.input(
                            "Subnet CIDR",
                            placeholder="e.g. 192.168.1.0/24",
                        ).classes("w-64")

                    check_result = ui.column().classes("w-full mt-4")

                    def check_ip_in_subnet():
                        check_result.clear()
                        with check_result:
                            try:
                                ip = ipaddress.ip_address(check_ip_input.value.strip())
                            except (ValueError, TypeError) as e:
                                ui.label(f"Invalid IP address: {e}").classes("text-red")
                                return

                            try:
                                network = ipaddress.ip_network(check_subnet_input.value.strip(), strict=False)
                            except (ValueError, TypeError) as e:
                                ui.label(f"Invalid subnet: {e}").classes("text-red")
                                return

                            if ip in network:
                                with ui.card().classes("w-full bg-green-100 dark:bg-green-900"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.icon("check_circle").classes("text-green text-2xl")
                                        ui.label(
                                            f"{ip} IS in subnet {network}"
                                        ).classes("text-lg font-semibold")
                            else:
                                with ui.card().classes("w-full bg-red-100 dark:bg-red-900"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.icon("cancel").classes("text-red text-2xl")
                                        ui.label(
                                            f"{ip} is NOT in subnet {network}"
                                        ).classes("text-lg font-semibold")

                    ui.button("Check", on_click=check_ip_in_subnet).props(
                        "color=primary icon=search"
                    ).classes("mt-2")
