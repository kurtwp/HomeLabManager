# Nmap Commands Reference

This document outlines the default nmap scan types available in the Home Lab Manager's Nmap Scanner page (Discovery → Nmap Scanner).

---

## Quick Scan Presets

These are available from the "Scan Type" dropdown on the Quick Scan tab.

### Ping Scan (Host Discovery Only)
```
nmap -sn <target>
```
- **What it does:** Discovers which hosts are alive without port scanning
- **Use case:** Quick count of active hosts on a subnet
- **Speed:** Fast (seconds for a /24)
- **Requires sudo:** No (but sudo gives ARP-based results on local networks)

---

### SYN Scan (Stealth Port Scan)
```
nmap -sS <target>
```
- **What it does:** Half-open TCP scan — sends SYN, waits for SYN-ACK, never completes handshake
- **Use case:** Discover open ports without being logged by most services
- **Speed:** Fast
- **Requires sudo:** Yes

---

### TCP Connect Scan (Full Connect)
```
nmap -sT <target>
```
- **What it does:** Full TCP three-way handshake on each port
- **Use case:** When you don't have root/sudo access
- **Speed:** Moderate
- **Requires sudo:** No

---

### Service Version Detection
```
nmap -sV <target>
```
- **What it does:** Probes open ports to determine service name and version
- **Use case:** Identify what software is running (e.g., Apache 2.4.52, OpenSSH 8.9)
- **Speed:** Slow (probes each open port)
- **Requires sudo:** No (but sudo improves accuracy)

---

### Service + OS Detection
```
nmap -sV -O <target>
```
- **What it does:** Service version detection plus TCP/IP fingerprinting to identify the operating system
- **Use case:** Full inventory — what OS and services each host runs
- **Speed:** Slow (especially on a /24)
- **Requires sudo:** Yes (OS detection requires raw packets)

---

### Aggressive Scan
```
nmap -A <target>
```
- **What it does:** Enables OS detection, version detection, script scanning, and traceroute
- **Use case:** Maximum information gathering for a thorough audit
- **Speed:** Very slow on large targets
- **Requires sudo:** Yes
- **Note:** This is noisy — services will log the scan

---

### Common Ports (1-1024)
```
nmap -p 1-1024 <target>
```
- **What it does:** Scans the well-known port range (1-1024)
- **Use case:** Quick check for standard services (HTTP, SSH, FTP, SMTP, etc.)
- **Speed:** Moderate
- **Requires sudo:** No

---

### All Ports (1-65535)
```
nmap -p- <target>
```
- **What it does:** Scans every possible TCP port
- **Use case:** Find services running on non-standard ports
- **Speed:** Very slow (especially without sudo)
- **Requires sudo:** Recommended (SYN scan is much faster)

---

## Timing Options

Available from the "Timing" dropdown:

| Option | Flag | Description |
|--------|------|-------------|
| Slow | `-T2` | IDS evasion, very cautious |
| Normal | `-T3` | Default nmap behavior |
| Fast | `-T4` | Recommended for local networks |
| Insane | `-T5` | Maximum speed, may miss results |

**Recommendation:** Use `-T4` for home lab scanning. Use `-T2` only if scanning production systems where you want to avoid triggering IDS/IPS alerts.

---

## Common Custom Commands

These can be entered on the "Custom Command" tab:

### Scan specific ports
```
-p 22,80,443,8080 192.168.2.0/24
```

### Top 20 most common ports
```
--top-ports 20 192.168.2.0/24
```

### UDP scan (find DNS, SNMP, DHCP)
```
-sU -p 53,67,68,161,162 192.168.2.0/24
```

### Scan a single host in detail
```
-A -T4 192.168.2.5
```

### Find web servers
```
-p 80,443,8080,8443 --open 192.168.2.0/24
```

### Detect only hosts with SSH
```
-p 22 --open 192.168.2.0/24
```

### Script scan for vulnerabilities
```
--script vuln 192.168.2.5
```

### Scan without DNS resolution (faster)
```
-n -sn 192.168.2.0/24
```

### Output with MAC addresses (requires sudo)
```
-sn 192.168.2.0/24
```

---

## Sudo Requirement

The "Run as root (sudo)" toggle prepends `sudo` to the nmap command. This is required for:

- **SYN scan** (`-sS`) — needs raw socket access
- **OS detection** (`-O`) — needs raw packets for TCP/IP fingerprinting
- **MAC address discovery** — ARP requests require elevated privileges
- **UDP scan** (`-sU`) — needs raw socket access

Without sudo, nmap falls back to slower TCP connect scans and cannot detect MAC addresses or OS.

### Setup (one-time on the server)
```bash
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/nmap" | sudo tee /etc/sudoers.d/nmap
sudo chmod 440 /etc/sudoers.d/nmap
```

---

## Tips

- **Start small:** Test on a single IP before scanning a full /24
- **Service + OS on /24:** Can take 15-30 minutes. Use `-T4` and enable sudo
- **Ping scan first:** Identify live hosts, then do detailed scans on specific IPs
- **Save results:** Click "Save to Database" after a scan to store OS/port info as notes on each IP
- **Local network advantage:** On a local subnet, nmap uses ARP which finds everything (even hosts blocking ICMP)

---

## Saved Results

When you click "Save to Database" after a scan:
- Each discovered host gets a **Note** titled "Nmap Scan Results"
- The note contains: OS detection, open ports (as a markdown table)
- The IP's `last_seen` and `status` are updated
- New IPs are created if they don't exist (requires a matching network in the DB)
- IPs outside the DHCP range are classified as Static
