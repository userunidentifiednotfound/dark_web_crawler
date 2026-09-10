#!/usr/bin/env bash
# ==============================================================================
# DWI DARK WEB & ONION INTELLIGENCE CRAWLER
# All-In-One Automated Installer & Launcher for Kali Linux / Debian
# ==============================================================================
set -e

# ANSI styling
BOLD="\033[1m"
GREEN="\033[0;32m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}${CYAN}"
cat << "EOF"
  ____  _       _____    ____                    _           
 |  _ \ \      / /_ _|  / ___|_ __ __ ___      _| | ___ _ __ 
 | | | \ \ /\ / / | |  | |   | '__/ _` \ \ /\ / / |/ _ \ '__|
 | |_| |\ V  V /  | |  | |___| | | (_| |\ V  V /| |  __/ |   
 |____/  \_/\_/  |___|  \____|_|  \__,_| \_/\_/ |_|\___|_|   
          DARK WEB & ONION INTELLIGENCE CRAWLER
EOF
echo -e "${RESET}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check root or sudo privileges
SUDO=""
if [ "$EUID" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then
        SUDO="sudo"
    else
        echo -e "${YELLOW}[!] Warning: sudo not found, running as current user.${RESET}"
    fi
fi

echo -e "${BOLD}[1/5] Updating package index & installing Kali Linux system packages...${RESET}"
$SUDO apt-get update -y
$SUDO apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    tor \
    torsocks \
    chromium \
    chromium-driver \
    curl \
    sqlite3 \
    libsqlite3-dev

echo -e "\n${BOLD}[2/5] Configuring and starting Tor SOCKS5 service...${RESET}"
# Ensure Tor service is running on default 127.0.0.1:9050
if command -v systemctl >/dev/null 2>&1; then
    $SUDO systemctl enable tor || true
    $SUDO systemctl start tor || true
elif command -v service >/dev/null 2>&1; then
    $SUDO service tor start || true
else
    # Fallback to direct daemon run if systemd not active
    tor --RunAsDaemon 1 || true
fi

# Quick Tor check
echo -n "Checking Tor SOCKS5 connectivity on 127.0.0.1:9050... "
if nc -z 127.0.0.1 9050 2>/dev/null || curl --socks5-hostname 127.0.0.1:9050 -s https://check.torproject.org >/dev/null 2>&1; then
    echo -e "${GREEN}ONLINE${RESET}"
else
    echo -e "${YELLOW}Tor daemon starting (or running on alternate port). Proceeding...${RESET}"
fi

echo -e "\n${BOLD}[3/5] Setting up dedicated Python Virtual Environment...${RESET}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo -e "\n${BOLD}[4/5] Installing Python dependencies & Chromium WebDriver bindings...${RESET}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e ".[browser,dev]"

# Ensure storage directories exist
mkdir -p storage/pages storage/screenshots

# Symlink executable into local path if writable
if [ -w "/usr/local/bin" ] || [ "$SUDO" != "" ]; then
    $SUDO ln -sf "$SCRIPT_DIR/dwi-crawler" /usr/local/bin/dwi-crawler 2>/dev/null || true
fi
chmod +x "$SCRIPT_DIR/dwi-crawler"

echo -e "\n${BOLD}[5/5] Installation Complete!${RESET}"
echo -e "${GREEN}✓ Kali Linux dependencies, Tor SOCKS5 proxy, and DWI Crawler are installed.${RESET}"
echo -e "${CYAN}Launching interactive CLI Dashboard now...${RESET}\n"
sleep 1

# Launch CLI Dashboard
"$SCRIPT_DIR/venv/bin/python3" "$SCRIPT_DIR/dwi-crawler" dashboard
