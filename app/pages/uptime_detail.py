"""Uptime Monitor detail page — heartbeat bar, stats, and latency graph."""

from nicegui import ui

from app.database.db import get_session_direct as get_session
from app.services.uptime_service import (
    get_monitor_by_id,
    get_ping_history,
    get_ping_stats,
    get_events_for_host,
    check_host,
)
from app.pages.layout import page_layout


def render_uptime_detail(monitor_id: int):
    """Render the uptime detail page for a single monitored host."""
    page_layout()

    session = get_session()
    host = get_monitor_by_id(session, monitor_id)

    if not host:
        with ui.column().classes("page-container"):
            ui.label("Monitor not found").classes("text-xl text-red")
        session.close()
        return

    with ui.column().classes("page-container w-full"):
        # Header
        with ui.row().classes("items-center gap-4"):
            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/uptime")).props(
                "flat round"
            )
            ui.label(host.name).classes("text-3xl font-bold")

        ui.label(host.ip_address).classes("text-lg font-mono text-gray-500")

        # Monitor type indicator
        monitor_type = getattr(host, 'monitor_type', 'ping') or 'ping'
        port = getattr(host, 'port', None)
        if monitor_type == "port" and port:
            with ui.row().classes("items-center gap-2"):
                ui.badge(f"TCP Port :{port}").props("color=teal")
                ui.label(f"Check every {host.check_interval} seconds").classes("text-sm text-gray-400")
        else:
            with ui.row().classes("items-center gap-2"):
                ui.badge("Ping (ICMP)").props("color=blue outline")
                ui.label(f"Check every {host.check_interval} seconds").classes("text-sm text-gray-400")

        ui.separator().classes("my-4")

        # Heartbeat bar + current status
        with ui.card().classes("w-full"):
            ping_history = get_ping_history(session, host.id, hours=1)

            with ui.row().classes("w-full items-center justify-between"):
                # Heartbeat bar — last ~30 checks as colored blocks
                with ui.row().classes("items-center gap-0"):
                    recent_pings = ping_history[-40:] if len(ping_history) > 40 else ping_history
                    if recent_pings:
                        for ping in recent_pings:
                            color = "#4ade80" if ping.is_up else "#ef4444"
                            ui.html(
                                f'<div style="width:8px; height:28px; background:{color}; '
                                f'border-radius:2px; margin:0 1px;" '
                                f'title="{ping.timestamp.strftime("%H:%M:%S") if ping.timestamp else ""}'
                                f' — {"UP" if ping.is_up else "DOWN"}'
                                f'{f" ({ping.latency_ms:.1f}ms)" if ping.latency_ms else ""}"></div>'
                            )
                    else:
                        ui.label("No data yet").classes("text-gray-400 text-sm italic")

                # Status badge
                status_color = {"up": "green", "down": "red", "unknown": "gray"}.get(
                    host.current_status, "gray"
                )
                ui.badge(host.current_status.upper()).props(
                    f"color={status_color}"
                ).classes("text-lg px-4 py-1")

            # Time range labels
            if ping_history:
                with ui.row().classes("w-full justify-between mt-1"):
                    first_time = ping_history[0].timestamp
                    if first_time:
                        from datetime import datetime, timezone
                        now = datetime.now(timezone.utc)
                        diff = now - first_time.replace(tzinfo=timezone.utc)
                        minutes_ago = int(diff.total_seconds() / 60)
                        ui.label(f"{minutes_ago}m ago").classes("text-xs text-gray-400")
                    else:
                        ui.label("").classes("text-xs")
                    ui.label("now").classes("text-xs text-gray-400")

        # Stats row
        stats_24h = get_ping_stats(session, host.id, hours=24)
        stats_30d = get_ping_stats(session, host.id, hours=720)  # 30 days

        with ui.card().classes("w-full mt-4"):
            with ui.row().classes("w-full justify-around"):
                _stat_block(
                    "Ping",
                    f"{stats_24h['current_latency']} ms" if stats_24h["current_latency"] else "—",
                    "(Current)",
                )
                _stat_block(
                    "Avg. Ping",
                    f"{stats_24h['avg_latency']} ms" if stats_24h["avg_latency"] else "—",
                    "(24-hour)",
                )
                _stat_block(
                    "Uptime",
                    f"{stats_24h['uptime_percent']}%" if stats_24h["total_checks"] else "—",
                    "(24-hour)",
                )
                _stat_block(
                    "Uptime",
                    f"{stats_30d['uptime_percent']}%" if stats_30d["total_checks"] else "—",
                    "(30-day)",
                )

        # Response time chart
        with ui.card().classes("w-full mt-4"):
            ui.label("Response Time").classes("text-lg font-semibold mb-2")

            # Time range selector
            chart_hours = {"value": 6}

            with ui.row().classes("justify-end mb-2"):
                time_range = ui.select(
                    {1: "1h", 3: "3h", 6: "6h", 12: "12h", 24: "24h"},
                    value=6,
                    label="Range",
                ).classes("w-24")

            chart_container = ui.column().classes("w-full")

            def render_chart():
                chart_container.clear()
                with chart_container:
                    hours = time_range.value
                    history = get_ping_history(session, host.id, hours=hours)

                    if not history:
                        ui.label("No ping data for this time range.").classes(
                            "text-gray-500 italic"
                        )
                        return

                    # Build chart data
                    timestamps = []
                    latencies = []

                    for ping in history:
                        time_str = ping.timestamp.strftime("%H:%M:%S") if ping.timestamp else ""
                        timestamps.append(time_str)
                        if ping.is_up and ping.latency_ms:
                            latencies.append(round(ping.latency_ms, 1))
                        else:
                            latencies.append(None)

                    # Calculate average for reference line
                    valid_latencies = [l for l in latencies if l is not None]
                    avg_latency = (
                        round(sum(valid_latencies) / len(valid_latencies), 1)
                        if valid_latencies else 0
                    )

                    # Build markArea for downtime periods (red vertical bands)
                    mark_area_data = []
                    i = 0
                    while i < len(history):
                        if not history[i].is_up:
                            start_idx = i
                            # Find end of downtime block
                            j = i
                            while j < len(history) and not history[j].is_up:
                                j += 1
                            end_idx = j - 1

                            # Use index-based xAxis to ensure visibility even for single points
                            # Extend single-point outages by 1 index to give them width
                            start_ts = timestamps[start_idx]
                            end_ts = timestamps[min(end_idx + 1, len(timestamps) - 1)] if end_idx == start_idx else timestamps[end_idx]

                            mark_area_data.append([
                                {"xAxis": start_ts},
                                {"xAxis": end_ts},
                            ])
                            i = j
                        else:
                            i += 1

                    chart_options = {
                        "tooltip": {
                            "trigger": "axis",
                            "formatter": "{b}<br/>Latency: {c} ms",
                        },
                        "grid": {
                            "left": "60",
                            "right": "20",
                            "top": "30",
                            "bottom": "50",
                        },
                        "xAxis": {
                            "type": "category",
                            "data": timestamps,
                            "axisLabel": {
                                "rotate": 0,
                                "interval": max(1, len(timestamps) // 8),
                                "formatter": "{value}",
                            },
                        },
                        "yAxis": {
                            "type": "value",
                            "name": "TCP Connect Time (ms)" if monitor_type == "port" else "Ping Latency (ms)",
                            "min": 0,
                        },
                        "series": [
                            {
                                "name": "Latency",
                                "type": "line",
                                "data": latencies,
                                "smooth": False,
                                "symbol": "none",
                                "lineStyle": {"color": "#22c55e", "width": 1.5},
                                "areaStyle": {"color": "rgba(34, 197, 94, 0.08)"},
                                "connectNulls": False,
                                "markLine": {
                                    "silent": True,
                                    "symbol": ["none", "arrow"],
                                    "data": [
                                        {
                                            "yAxis": avg_latency,
                                            "label": {
                                                "formatter": f"avg",
                                                "position": "end",
                                            },
                                            "lineStyle": {"color": "#93c5fd", "type": "dashed", "width": 1},
                                        }
                                    ],
                                },
                                "markArea": {
                                    "silent": True,
                                    "itemStyle": {
                                        "color": "rgba(239, 68, 68, 0.25)",
                                        "borderColor": "rgba(239, 68, 68, 0.6)",
                                        "borderWidth": 1,
                                    },
                                    "data": mark_area_data,
                                } if mark_area_data else {},
                            }
                        ],
                    }

                    ui.echart(chart_options).classes("w-full h-72")

            time_range.on("update:model-value", lambda: render_chart())
            render_chart()

        # Recent events
        with ui.card().classes("w-full mt-4"):
            ui.label("Recent Events").classes("text-lg font-semibold mb-2")
            events = get_events_for_host(session, host.id, limit=20)

            if events:
                for event in events:
                    ev_color = {"down": "red", "recovered": "green", "up": "green"}.get(
                        event.event_type, "gray"
                    )
                    with ui.row().classes("items-center gap-2 mb-1"):
                        ui.icon("circle").classes(f"text-xs text-{ev_color}")
                        ui.label(
                            event.timestamp.strftime("%Y-%m-%d %H:%M:%S") if event.timestamp else "—"
                        ).classes("text-xs text-gray-400 w-40")
                        ui.badge(event.event_type.upper()).props(f"color={ev_color}").classes("text-xs")
                        if event.details:
                            ui.label(event.details).classes("text-xs text-gray-500")
                        if event.latency_ms:
                            ui.label(f"{event.latency_ms:.1f}ms").classes("text-xs text-gray-400")
            else:
                ui.label("No events recorded yet.").classes("text-gray-500 italic")

    session.close()


def _stat_block(title: str, value: str, subtitle: str):
    """Render a stats block (like Ping, Avg. Ping, Uptime)."""
    with ui.column().classes("items-center gap-0"):
        ui.label(title).classes("text-sm font-semibold")
        ui.label(subtitle).classes("text-xs text-gray-400")
        ui.label(value).classes("text-lg font-bold text-primary mt-1")
