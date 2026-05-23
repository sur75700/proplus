#!/usr/bin/env bash
set -euo pipefail

echo "============================================================"
echo " IP is a shadow, presence is an illusion. 🕶️"
echo " READY. Ghost mode ON. 👻"
echo "============================================================"
echo

echo "[1] Tor status"
torsocks curl -s https://check.torproject.org/api/ip || true
echo
echo

echo "[2] Public IP comparison"
echo -n "NORMAL IP: "
curl -s https://api.ipify.org || true
echo
echo -n "TOR IP:    "
torsocks curl -s https://api.ipify.org || true
echo
echo

echo "[3] Local interfaces"
ip -br a
echo

echo "[4] Listening TCP services"
sudo ss -ltnp
echo

echo "[5] Firewall status"
sudo ufw status verbose || true
echo

echo "[6] Established connections"
sudo ss -tpn state established || true
echo

echo "[7] Local self-scan"
LAN_IP="$(ip -4 addr show wlan0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 || true)"
if [[ -n "${LAN_IP:-}" ]]; then
  echo "Scanning: $LAN_IP"
  nmap -sS -Pn "$LAN_IP"
else
  echo "wlan0 IP not found, skipping self-scan."
fi
echo

echo "============================================================"
echo "[FINAL] IP is a shadow, presence is an illusion. 🕶️"
echo "[STATUS] READY"
echo "[MODE] Ghost mode ON. 👻"
echo "============================================================"
