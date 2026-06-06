# Home Lab IP Management & Equipment Tracker

A comprehensive single-user application for managing IP addresses, networks, VLANs, and equipment in your home lab environment. Track DHCP/static assignments, document configurations, store troubleshooting solutions, and maintain a searchable knowledge base—all in one place.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![NICEGUI](https://img.shields.io/badge/NICEGUI-Modern%20UI-green)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightblue)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

### Core Functionality (Phase 1)
- **Network & VLAN Management**: Track networks, VLANs, and hierarchical subnet organization
- **IP Address Tracking**: Monitor static vs DHCP assignments, view available IP space
- **Automatic Network Scanning**: Discover devices, auto-populate IPs, remove offline devices
- **Visual Subnet Display**: Graphical representation of IP allocation and usage
- **Device Inventory**: Manage device types, track equipment, link devices to IPs
- **Markdown Documentation**: 
  - Per-IP device notes
  - Per-network/VLAN documentation
  - Per-device notes with full markdown support
- **Knowledge Base**: Store how-to guides, troubleshooting solutions, and procedures
- **Change Tracking**: Comprehensive changelog of all modifications with scan events
- **Tagging & Labeling**: Categorize IPs and devices (investigate, temporary, trusted, production, etc.)
- **Search & Filter**: Global search across all notes, documentation, and data
- **Import/Export**: CSV import for bulk additions, CSV/Excel export for backup

### Phase 2 Enhancements
- Advanced IP management (nested subnets, IPv4/IPv6 calculator)
- Custom fields for devices, IPs, networks, and VLANs
- Scheduled automatic scans with configurable frequency
- Physical location tracking and rack management
- Documentation templates and versioning
- Advanced reporting and visualization
- **Ubiquiti UniFi Integration** (optional):
  - Auto-discover devices from UniFi Controller
  - Pull VLAN configurations
  - Sync device names and statuses
  - Monitor network performance metrics

### Phase 3 (Future)
- REST API for automation
- Mobile app or responsive improvements
- Advanced automation (DNS, DHCP integration)
- Network diagram generation
- Cable management tracking

---

## Screenshots

*Coming soon - Add screenshots of dashboard, network view, documentation, etc.*

---

## Tech Stack

- **Backend**: Python 3.10+
- **Frontend**: NICEGUI with HTML, CSS, and JavaScript
- **Database**: SQLite (single-file, easy backup)
- **Network Scanning**: python-nmap, ping3
- **Task Scheduling**: APScheduler (for scheduled scans)
- **Data Validation**: Pydantic
- **Markdown**: markdown-it-py
- **Data Export**: openpyxl, xlsxwriter
- **Ubiquiti Integration**: requests (UniFi API)

---

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- nmap (for network scanning)
  - Ubuntu/Debian: `sudo apt install nmap`
  - Windows: Download from [nmap.org](https://nmap.org)
  - macOS: `brew install nmap`

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/home-lab-manager.git
   cd home-lab-manager
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the app**
   - Open your browser and navigate to: `http://localhost:8080`
   - The database (`home_lab_manager.db`) will be created automatically

---

## Usage

### Quick Start

1. **Add Networks**: Create your networks/VLANs with CIDR notation
   - Example: `192.168.1.0/24` (Home Network)
   - Example: `192.168.50.0/24` (IoT Network)

2. **Scan Networks**: Run a network scan to discover devices
   - Manual scan anytime
   - Scheduled scans (Phase 2)
   - IPs are automatically added/removed based on what's found

3. **Document Everything**: Add markdown notes to IPs, devices, networks
   - Device configuration notes
   - Troubleshooting history
   - Link related devices

4. **Build Knowledge Base**: Create how-to guides and procedures
   - "How to configure VLAN"
   - "How I fixed printer connectivity"
   - Reference devices/IPs from documentation

5. **Search & Find**: Search across all notes and documentation
   - Find notes by device IP
   - Search troubleshooting solutions
   - Filter by tags

### Example Workflow

```markdown
# Add a network
Network: Home Lab
VLAN ID: 100
Subnet: 192.168.100.0/24
Description: Main home lab network for servers and VMs

# Run a scan
Discover devices on 192.168.100.0/24
[Found: 5 devices, Free IPs: 245]

# Document a device
Device: Proxmox Server
IP: 192.168.100.10 (Static)
Notes:
- Host for VMs and containers
- Requires static IP for management
- Connected to storage NAS via NFS

# Create knowledge base article
Title: "How to Add a New VM to Proxmox"
- Access Web UI at 192.168.100.10:8006
- Create VM with static IP reservation
- Configure NFS mount points
```

---

## Deployment

### Windows 11 / Ubuntu Desktop (Development)

```bash
source venv/bin/activate  # Linux/macOS
python main.py            # Or python3 main.py
```

### Ubuntu Server (Production)

1. **Install and setup**
   ```bash
   cd /opt
   sudo git clone https://github.com/yourusername/home-lab-manager.git
   cd home-lab-manager
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Create systemd service**
   - Copy the service file (see documentation)
   - Enable auto-start on boot

3. **Run as a service**
   ```bash
   sudo systemctl enable home-lab-manager
   sudo systemctl start home-lab-manager
   ```

4. **Access the application**
   ```
   http://your-server-ip:8080
   ```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed setup instructions.

---

## Project Structure

```
home-lab-manager/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── config.py              # Configuration settings
├── home_lab_manager.db    # SQLite database (auto-created)
│
├── app/
│   ├── models/            # Database models
│   ├── database/          # Database operations
│   ├── pages/             # NICEGUI UI pages
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
│
├── static/                # CSS, images
├── tests/                 # Unit tests
└── docs/                  # Documentation
```

---

## Development Roadmap

### Phase 1 ✅ (In Progress)
- [x] Core IP and VLAN management
- [x] Network scanning
- [x] Markdown documentation
- [x] Knowledge base
- [ ] Basic UI implementation
- [ ] Testing

### Phase 2 📋 (Planned)
- [ ] Custom fields
- [ ] Scheduled scanning
- [ ] Physical location tracking
- [ ] Ubiquiti UniFi integration
- [ ] Advanced reporting
- [ ] Documentation templates

### Phase 3 🎯 (Future)
- [ ] REST API
- [ ] Mobile experience
- [ ] Advanced automation
- [ ] Network diagrams
- [ ] Additional integrations

---

## Configuration

Edit `config.py` to customize:

```python
# Network scanning
NMAP_TIMEOUT = 60  # seconds
SCAN_THREADS = 4

# Database
DATABASE_PATH = 'home_lab_manager.db'

# Web server
HOST = '127.0.0.1'  # or '0.0.0.0' for network access
PORT = 8080

# Ubiquiti integration (Phase 2)
UNIFI_HOST = ''
UNIFI_USERNAME = ''
UNIFI_PASSWORD = ''
```

For production deployment, use environment variables:
```bash
export APP_ENV=production
export APP_PORT=8080
export UNIFI_HOST=192.168.1.1
```

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support & Documentation

- **Full Feature List**: See [FEATURES.md](docs/FEATURES.md)
- **Deployment Guide**: See [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Database Schema**: See [DATABASE.md](docs/DATABASE.md)
- **API Reference**: Coming soon (Phase 3)

### Getting Help

- Check the [Knowledge Base](/docs/knowledge-base) in this repo
- Open an [Issue](https://github.com/yourusername/home-lab-manager/issues)
- Start a [Discussion](https://github.com/yourusername/home-lab-manager/discussions)

---

## Acknowledgments

- Inspired by phpIPAM and other IP management tools
- Built with NICEGUI for beautiful Python UIs
- Uses SQLAlchemy for database management
- Network scanning powered by nmap

---

## Roadmap Updates

Check the [Projects](https://github.com/yourusername/home-lab-manager/projects) tab for current development status and upcoming features.

---

## Author

Created for home lab enthusiasts who want to manage their networks like professionals.

If you find this useful, please give it a ⭐ star!

---

**Last Updated**: 2024-02-04
**Current Version**: 0.1.0 (Development)
