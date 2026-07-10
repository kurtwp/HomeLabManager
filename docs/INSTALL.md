# Installation Guide — Home Lab IP Manager

This guide covers installing the Home Lab IP Manager on an Ubuntu server (tested on 24.04 and 26.04).

---

## Requirements

- Ubuntu 22.04, 24.04, or 26.04 (any Linux with systemd works)
- Python 3.12 (3.14 is NOT supported due to pydantic-core compatibility)
- nmap (for network scanning)
- snmp tools (for SNMP discovery)
- Git

---

## Step 1: Install System Dependencies

```bash
sudo apt update
sudo apt install git nmap snmp snmp-mibs-downloader
```

### Python 3.12

Ubuntu 26.04 ships with Python 3.14 which is too new for some dependencies. Install 3.12 via deadsnakes PPA:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

For Ubuntu 24.04 or earlier, Python 3.12 is likely already available:

```bash
sudo apt install python3.12 python3.12-venv
```

Verify:

```bash
python3.12 --version
# Python 3.12.x
```

---

## Step 2: Clone the Repository

```bash
cd /opt
sudo git clone https://github.com/kurtwp/HomeIPAdmin.git
sudo chown -R $USER:$USER /opt/HomeIPAdmin
cd /opt/HomeIPAdmin
```

---

## Step 3: Create Virtual Environment and Install Dependencies

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Step 4: Configure Environment

```bash
cp .env.example .env
nano .env
```

Edit the following values:

```bash
# Required
DATABASE_URL=sqlite:///./home_lab_manager.db
APP_TITLE=Home Lab Manager
APP_PORT=80

# UniFi Integration (optional — leave defaults if you don't have UniFi)
UNIFI_API_KEY=your_local_api_key
UNIFI_BASE_URL=https://192.168.x.x
UNIFI_SITE_ID=your_site_uuid

# UniFi Cloud / Site Manager (optional)
UNIFI_CLOUD_API_KEY=your_cloud_key
```

### Getting API Keys

- **Local Network API Key**: Sign into your UniFi console → Integrations → Create API Key
- **Cloud Site Manager Key**: Sign into unifi.ui.com → Settings → API Keys → Create

If you don't have UniFi hardware, leave these as the defaults — the app works without them using ping/nmap scanning.

---

## Step 5: Allow Nmap Without Password (Optional but Recommended)

```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/nmap" | sudo tee /etc/sudoers.d/nmap
sudo chmod 440 /etc/sudoers.d/nmap
```

This enables the Nmap Scanner page to run privileged scans (SYN scan, OS detection) without prompting for a password.

---

## Step 6: Test the Application

```bash
cd /opt/HomeIPAdmin
source .venv/bin/activate
python main.py
```

You should see:

```
NiceGUI ready to go on http://localhost, and http://<your-server-ip>
```

Press Ctrl+C to stop the test.

---

## Step 7: Create Systemd Service

Copy the included service file:

```bash
sudo cp /opt/HomeIPAdmin/homeipmanager.service /etc/systemd/system/
```

Edit if needed (default runs as root for port 80 binding):

```bash
sudo nano /etc/systemd/system/homeipmanager.service
```

Contents:

```ini
[Unit]
Description=Home Lab IP Manager
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/HomeIPAdmin
Environment="PATH=/opt/HomeIPAdmin/.venv/bin:/usr/bin:/bin"
ExecStart=/opt/HomeIPAdmin/.venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **Note**: The service runs as root to bind to port 80. For a home lab this is fine.
> To run on port 8080 as a regular user instead, change `User=youruser`, `Group=youruser`
> and set `APP_PORT=8080` in `.env`.

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable homeipmanager
sudo systemctl start homeipmanager
```

Check status:

```bash
sudo systemctl status homeipmanager
```

---

## Step 8: Access the Application

Open a browser and navigate to:

```
http://<server-ip>
```

For example: `http://192.168.2.1`

---

## Updating

When new code is pushed to GitHub:

```bash
cd /opt/HomeIPAdmin
sudo git pull
sudo systemctl restart homeipmanager
```

---

## Backup

Only two files need to be backed up:

| File | Description |
|------|-------------|
| `.env` | API keys and configuration |
| `home_lab_manager.db` | All application data |

### Automated Daily Backup

Create `/home/blah/backups/backup_homeip.sh`:

```bash
#!/bin/bash
BACKUP_DIR=/home/blah/backups/homeipmanager
mkdir -p $BACKUP_DIR
cp /opt/HomeIPAdmin/.env $BACKUP_DIR/.env
cp /opt/HomeIPAdmin/home_lab_manager.db $BACKUP_DIR/home_lab_manager_$(date +%Y%m%d).db
# Keep only last 7 days
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
```

```bash
chmod +x /home/blah/backups/backup_homeip.sh
crontab -e
# Add this line:
0 2 * * * /home/blah/backups/backup_homeip.sh
```

### Restore

```bash
cd /opt
sudo git clone https://github.com/kurtwp/HomeIPAdmin.git
sudo chown -R $USER:$USER /opt/HomeIPAdmin
cd /opt/HomeIPAdmin
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp /path/to/backup/.env .env
cp /path/to/backup/home_lab_manager_YYYYMMDD.db home_lab_manager.db
sudo systemctl restart homeipmanager
```

---
## Update HomeIPAdmin
To update it in the future when you push new code:
```
cd /opt/HomeIPAdmin
sudo git pull
sudo systemctl restart homeipmanager
```
## Troubleshooting

### Check logs

```bash
sudo journalctl -u homeipmanager -n 50 --no-pager
```

### ModuleNotFoundError

Reinstall dependencies:

```bash
cd /opt/HomeIPAdmin
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart homeipmanager
```

### Port 80 permission denied

Ensure the service runs as root, or use port 8080:

```bash
# Option A: Run as root (for port 80)
sudo sed -i 's/User=.*/User=root/' /etc/systemd/system/homeipmanager.service
sudo sed -i 's/Group=.*/Group=root/' /etc/systemd/system/homeipmanager.service
sudo systemctl daemon-reload
sudo systemctl restart homeipmanager

# Option B: Use port 8080 (no root needed)
# Edit .env: APP_PORT=8080
# Edit service: User=youruser, Group=youruser
```

### Python 3.14 compatibility error

If you see errors about `PyO3` or `pydantic-core` failing to build:

```
error: the configured Python interpreter version (3.14) is newer than PyO3's maximum supported version
```

You must use Python 3.12 or 3.13. Install via deadsnakes PPA:

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv
cd /opt/HomeIPAdmin
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Database locked

If you see SQLite "database is locked" errors, ensure only one instance is running:

```bash
sudo systemctl stop homeipmanager
# Kill any stray processes
pkill -f "python main.py"
sudo systemctl start homeipmanager
```

---

## Architecture

```
/opt/HomeIPAdmin/
├── main.py              # Application entry point
├── config.py            # Environment-based configuration
├── .env                 # Secrets and settings (NOT in git)
├── home_lab_manager.db  # SQLite database (NOT in git)
├── requirements.txt     # Python dependencies
├── homeipmanager.service # Systemd unit file
├── app/
│   ├── database/        # SQLAlchemy setup
│   ├── models/          # ORM models
│   ├── pages/           # NiceGUI UI pages
│   ├── services/        # Business logic
│   └── utils/           # Helpers
└── static/              # CSS
```
