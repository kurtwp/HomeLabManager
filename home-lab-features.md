# Home Lab IP Management & Equipment Application - Phased Feature List

---

## Phase 1 (MVP) - Core Functionality

### Network & IP Management
- Network/VLAN tracking with hierarchical organization
- Visual subnet display showing IP allocation graphically
- Automatic free space calculation for each subnet/VLAN
- Distinguish between static and DHCP IP assignments
- Manual network scanning to auto-populate database
- Automatic IP addition when devices are found
- Automatic IP removal when devices are not found during scan
- Hostname resolution during scans

### Documentation & Notes
- Per-IP markdown notes
- Per-network/VLAN markdown documentation
- Per-device markdown notes
- **Knowledge base / How-to documentation section**
- **Troubleshooting guides for solved issues**
- **Procedures/runbooks for common tasks**
- Link documentation to specific IPs, devices, or networks
- Markdown editor with preview capability

### Device Management
- Basic device inventory tracking
- Device types categorization
- Link devices to IP addresses

### Organization & Discovery
- Simple tags/labels system (investigate, temporary, trusted, guest, production, etc.)
- Color coding for visual categorization
- Global search across all notes, IPs, devices, and documentation
- Filter by network, VLAN, device type, tags

### History & Tracking
- Comprehensive changelog tracking all modifications
- Per-IP change history (when added, removed, modified)
- Scan event log with timestamps
- Ability to add comments/notes to changelog entries
- Historical note preservation when IPs are removed

### Data Management
- CSV import for bulk IP additions
- CSV export for backup or reporting
- Basic backup/restore

### UI Essentials
- Dashboard showing network overview
- Quick-add IP/device forms
- Recently modified IPs/devices view

---

## Phase 2 (Enhanced Features)

### Advanced IP Management
- Nested subnet support (e.g., /24 subdivided into /26s)
- IPv4/IPv6 calculator built-in
- Favorite networks for quick access
- VRF support for routing isolation
- Visual subnet maps showing nested relationships

### Advanced Device Management
- Physical location tracking (room, rack position, shelf)
- Rack management for equipment layout visualization
- Device images/photos upload

### Custom Fields & Metadata
- Custom field support for IPs, devices, subnets, VLANs
- Multiple field types: text, number, dropdown/select, date, checkbox
- Mark fields as required or optional
- Set default values
- Examples: Warranty expiration, Purchase date, Service tag, MAC address, Port number

### Automation & Scheduling
- Scheduled automatic scans (cron/scheduled tasks)
- Configurable scan frequency per network
- Thread/parallel scanning for faster results
- Automatic hostname updates from DNS/mDNS

### Documentation Enhancements
- Documentation templates for common tasks
- Documentation versioning/history
- Categories/folders for knowledge base organization
- Advanced cross-referencing between docs and resources

### Reporting & Visualization
- Subnet utilization charts/graphs
- Networks approaching capacity warnings
- Usage reports over time
- Device inventory reports

### Advanced Search & Filtering
- Advanced filtering (by date range, status, custom fields)
- Saved search queries
- Search within specific date ranges

### Import/Export
- Excel import/export
- Export subnet documentation
- Bulk operations via import

### Ubiquiti Integration (Optional)
- UniFi Controller API integration
- Auto-discovery of Ubiquiti devices (APs, switches, gateways, Dream Machine Pro, etc.)
- Pull VLAN configurations from UniFi controller
- Sync device names and descriptions from UniFi
- Real-time client/device status from UniFi
- Pull DHCP assignments and reservations from UniFi DHCP server
- Monitor network performance metrics (latency, bandwidth, etc.)
- Auto-sync device inventory with UniFi controller data
- OneLogin/SSO integration if using Ubiquiti cloud
- Identify and track guest networks and isolated VLANs
- Support for UniFi devices (UniFi Dream Machine Pro, UniFi switches, access points, etc.)

---

## Phase 3 (Advanced/Future)

### API & Integration
- REST API for automation and integration
- Webhook support for external integrations
- Integration with monitoring tools (Prometheus, Grafana, etc.)

### Mobile Experience
- Mobile-responsive design improvements
- Native mobile app (optional)
- Offline capability with sync

### Advanced Automation
- DNS integration (PowerDNS, etc.)
- DHCP server integration
- Automatic device discovery via SNMP
- Integration with network equipment APIs (UniFi, pfSense, etc.)

### Collaboration Features (if expanding beyond single-user)
- Multi-user support with permissions
- Email notifications for changes
- IP request/approval workflows
- User activity logging

### Advanced Features
- NAT management
- Port forwarding documentation
- Network diagram generation
- Cable management tracking
- Service/application mapping to IPs

---

## Features Deferred/Out of Scope

These are not planned for the single-user home lab use case:

- LDAP/AD authentication
- Complex multi-tenancy
- Enterprise-level compliance features
- Advanced billing/chargeback
- SLA tracking

---

## Recommended Implementation Order

### Start Here (Phase 1 - Weeks 1-4)
1. Database schema + basic CRUD for networks, IPs, devices
2. Simple network scanner
3. Markdown notes on IPs and devices
4. Basic search
5. Changelog/history

### Next (Phase 1 - Weeks 5-8)
6. Visual subnet display
7. Knowledge base/documentation section
8. Tags and filtering
9. Dashboard and overview pages
10. Import/export CSV

### Then Move to Phase 2
Once Phase 1 is stable and you've used it for a few weeks.

---

## Example Use Cases

### Knowledge Base Documentation Example
```markdown
## How-To: Configure VLAN on UniFi Switch
1. Access controller at 192.168.1.10
2. Navigate to Settings > Networks
3. Create new network with VLAN ID
...

## Troubleshooting: Printer Keeps Disconnecting
**Problem**: HP Printer (192.168.50.100) drops connection every 2-3 days
**Solution**: Assigned static IP, disabled power saving mode
**Related devices**: Router (192.168.1.1), Switch (192.168.1.2)
**Date solved**: 2024-02-04
```

### Per-IP Note Example
```markdown
## Device: HP Printer (Office)
**Last seen**: 2024-02-04 14:30

### Configuration
- Static IP: Required (DHCP causes issues)
- Port forwarding: None needed
- VLAN: IoT (isolated from main network)

### Troubleshooting History
- [ ] Check if firmware needs update
- [x] Reset network settings - 2024-01-15
- [x] Assigned static IP - 2024-01-15

### Notes
Drops connection every 2-3 days. Seems related to router reboots.
See related: `192.168.1.1` (router)
```

---

## Technical Considerations

### Database Schema (Suggested Tables)
- `networks` - Subnet/VLAN definitions
- `ip_addresses` - Individual IP entries
- `devices` - Physical/virtual equipment
- `device_types` - Categories of devices
- `tags` - Labeling system
- `documentation` - Knowledge base articles
- `changelog` - History tracking
- `scan_logs` - Network scan results
- `custom_fields` - User-defined fields (Phase 2)
- `locations` - Physical locations (Phase 2)

### Technology Stack Considerations

**Chosen Stack:**
- **Backend**: Python (Flask/FastAPI integration with NICEGUI)
- **Frontend**: NICEGUI with HTML, CSS, and JavaScript
- **Database**: SQLite

**Recommended Python Libraries:**
- **Web Framework**: NICEGUI (Python UI framework)
- **Database ORM**: SQLAlchemy with SQLite
- **Markdown Rendering**: markdown-it-py or mistune for markdown parsing
- **Network Scanning**: nmap-python, python-nmap, or ping3 for ICMP
- **Data Export**: openpyxl or xlsxwriter for Excel/CSV export
- **API Clients**: 
  - `requests` for HTTP calls to UniFi Controller API
  - `unifi-api` library (if available) or custom requests wrapper
- **Scheduling**: APScheduler for scheduled network scans
- **Utilities**: 
  - `python-dateutil` for date handling
  - `python-dotenv` for configuration management
  - `pydantic` for data validation

**Database:**
- SQLite with SQLAlchemy ORM
- Database file: `home_lab_manager.db`
- Simple single-file database (perfect for single-user home lab)
- Easy backup (just copy the .db file)

**Frontend Considerations with NICEGUI:**
- NICEGUI provides reactive UI components
- Markdown support via NICEGUI's built-in markdown display
- Chart/graph support via NICEGUI's charting components or Chart.js
- Real-time updates with NICEGUI's data binding
- Responsive design out of the box
- Can embed custom HTML/CSS/JavaScript as needed

**Ubiquiti Integration (Phase 2):**
- `requests` library for UniFi Controller REST API calls
- Handle UniFi authentication (username/password or API token)
- Requires UniFi Controller 6.0+ (or UniFi Dream Machine)

---

## Project Structure (Recommended)

```
home-lab-manager/
├── main.py                 # NICEGUI app entry point
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── .env.example           # Environment variables template
├── home_lab_manager.db    # SQLite database (auto-created)
│
├── app/
│   ├── __init__.py
│   ├── models/            # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── network.py     # Network/VLAN models
│   │   ├── ip_address.py  # IP address models
│   │   ├── device.py      # Device models
│   │   ├── documentation.py # Knowledge base models
│   │   ├── changelog.py   # History/changelog models
│   │   └── tag.py         # Tag/label models
│   │
│   ├── database/          # Database operations
│   │   ├── __init__.py
│   │   └── db.py          # SQLAlchemy setup, session management
│   │
│   ├── pages/             # NICEGUI page components
│   │   ├── __init__.py
│   │   ├── dashboard.py   # Main dashboard
│   │   ├── networks.py    # Network management
│   │   ├── devices.py     # Device management
│   │   ├── documentation.py # Knowledge base
│   │   ├── ips.py         # IP address details
│   │   └── settings.py    # App settings
│   │
│   ├── services/          # Business logic
│   │   ├── __init__.py
│   │   ├── scanner.py     # Network scanning logic
│   │   ├── markdown_handler.py # Markdown rendering
│   │   ├── ubiquiti_sync.py # UniFi API integration
│   │   ├── export.py      # Import/export functionality
│   │   └── changelog.py   # Change tracking logic
│   │
│   └── utils/             # Utility functions
│       ├── __init__.py
│       ├── validators.py  # IP/CIDR validation
│       ├── formatters.py  # Data formatting
│       └── constants.py   # App constants
│
├── static/                # Static files (CSS, images)
│   ├── custom.css
│   └── images/
│
└── tests/                 # Unit tests (Phase 2+)
    ├── __init__.py
    ├── test_scanner.py
    ├── test_models.py
    └── test_services.py
```

---

## Getting Started with NICEGUI + SQLite

### Installation
```bash
pip install nicegui sqlalchemy sqlite3 python-nmap requests apscheduler pydantic markdown-it-py
```

### Basic Project Setup
```python
# main.py
from nicegui import ui
from app.database.db import init_db, get_session
from app.pages import dashboard, networks, devices, documentation

# Initialize database
init_db()

# Define UI pages
@ui.page('/')
def home():
    dashboard.render_dashboard()

@ui.page('/networks')
def networks_page():
    networks.render_networks()

@ui.page('/devices')
def devices_page():
    devices.render_devices()

@ui.page('/docs')
def documentation_page():
    documentation.render_knowledge_base()

# Run app
ui.run(title='Home Lab Manager', native=False, port=8080)
```

### SQLite Setup with SQLAlchemy
```python
# app/database/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./home_lab_manager.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()
```

---

## Development Workflow for NICEGUI

1. **Models First**: Define all SQLAlchemy models
2. **Database Layer**: Create database helper functions in services
3. **UI Components**: Build NICEGUI pages that interact with database
4. **Markdown Support**: Integrate markdown rendering for notes
5. **Network Scanner**: Develop scanning service
6. **Testing**: Write unit tests as you go

---

