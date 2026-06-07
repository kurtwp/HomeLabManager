# Home Lab IP Manager

A self-hosted IP address management (IPAM) and equipment tracking application for home labs. Built with Python, NiceGUI, and SQLite.

## Features

- **Network/VLAN tracking** with visual subnet maps showing IP allocation
- **Device inventory** with type categorization and manufacturer/model info
- **IP address management** — static, DHCP, reserved assignments with status tracking
- **Network scanning** — discover hosts via nmap or ICMP, auto-add/remove IPs, resolve hostnames
- **Markdown notes** on IPs, devices, and networks with live preview
- **Knowledge base** — how-to guides, troubleshooting docs, and runbooks
- **Tags & labels** with color coding for visual organization
- **Global search** across all entities
- **Changelog** — full audit history of all changes
- **CSV import/export** for bulk operations and backup
- **Dashboard** with utilization stats, recent activity, and quick-add forms

## Screenshots

*(Coming soon)*

## Quick Start

```bash
# Clone the repo
git clone https://github.com/kurtwp/HomeIPAdmin.git
cd HomeIPAdmin

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the app
python main.py
```

Open http://localhost:8080 in your browser.

## Requirements

- Python 3.11+
- nmap (optional, for network scanning — falls back to ICMP ping)

## Configuration

Copy `.env.example` to `.env` and set your values:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///./home_lab_manager.db` |
| `APP_TITLE` | Browser tab title | `Home Lab Manager` |
| `APP_PORT` | Web server port | `8080` |
| `UNIFI_API_KEY` | UniFi Network API key (Phase 2) | — |
| `UNIFI_BASE_URL` | UniFi console URL | `https://192.168.2.254` |
| `UNIFI_SITE_ID` | UniFi site UUID | — |

## Project Structure

```
HomeIPAdmin/
├── main.py                    # App entry point and page routing
├── config.py                  # Environment-based configuration
├── requirements.txt           # Python dependencies
├── .env.example               # Config template
├── static/custom.css          # Custom styles
└── app/
    ├── database/db.py         # SQLAlchemy setup
    ├── models/                # ORM models (Network, IP, Device, Tag, etc.)
    ├── pages/                 # NiceGUI page components
    ├── services/              # Business logic (CRUD, scanner, changelog)
    └── utils/                 # Validators, formatters, constants
```

## Tech Stack

- **Backend**: Python 3.12
- **UI Framework**: [NiceGUI](https://nicegui.io/)
- **Database**: SQLite via SQLAlchemy
- **Scanning**: python-nmap / ping3
- **Markdown**: markdown-it-py

## Roadmap

- [x] Phase 1A: Core CRUD, scanner, notes, search, changelog
- [x] Phase 1B: Subnet grid, tags, CSV import/export, quick-add
- [ ] Phase 2: UniFi API integration, scheduled scans, custom fields
- [ ] Phase 3: REST API, reporting, mobile-responsive design

See [home-lab-features.md](home-lab-features.md) for the full feature roadmap.

## License

MIT
