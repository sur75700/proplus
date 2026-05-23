#!/usr/bin/env bash
set -u

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

fail_count=0
warn_count=0

ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; warn_count=$((warn_count+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $*"; fail_count=$((fail_count+1)); }
info() { echo -e "${BLUE}[INFO]${NC} $*"; }

banner() {
  echo "============================================================"
  echo " IP is a shadow, presence is an illusion. 🕶️"
  echo " READY. Ghost mode ON. 👻"
  echo "============================================================"
  echo
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    fail "Missing command: $1"
    return 1
  }
}

section() {
  echo
  echo "------------------------------------------------------------"
  echo "$1"
  echo "------------------------------------------------------------"
}

banner

for cmd in curl torsocks ip ss nmap awk grep sed tail; do
  need_cmd "$cmd" || true
done

section "[1] Tor status"
tor_json="$(torsocks curl -s https://check.torproject.org/api/ip 2>&1)"
echo "$tor_json"

if echo "$tor_json" | grep -q '"IsTor":true'; then
  ok "Tor status confirmed."
else
  fail "Tor status is NOT confirmed."
fi

tor_ip="$(echo "$tor_json" | sed -n 's/.*"IP":"\([^"]*\)".*/\1/p')"
[[ -n "${tor_ip:-}" ]] && info "Tor IP: $tor_ip"

section "[2] Public IP comparison"
normal_ip="$(curl -s https://api.ipify.org 2>/dev/null || true)"
tor_exit_ip="$(torsocks curl -s https://api.ipify.org 2>/dev/null || true)"

echo "NORMAL IP: ${normal_ip:-unknown}"
echo "TOR IP:    ${tor_exit_ip:-unknown}"

if [[ -z "${normal_ip:-}" || -z "${tor_exit_ip:-}" ]]; then
  fail "Could not retrieve one or both public IPs."
elif [[ "$normal_ip" == "$tor_exit_ip" ]]; then
  fail "Normal IP and Tor IP are identical. Possible leak / Tor not being used for this check."
else
  ok "Normal IP and Tor IP differ."
fi

section "[3] Local interfaces"
ip -br a

lan_ip="$(ip -4 -br a | awk '$1=="wlan0"{print $3}' | cut -d/ -f1)"
if [[ -n "${lan_ip:-}" ]]; then
  ok "Detected LAN IP on wlan0: $lan_ip"
else
  warn "Could not detect wlan0 LAN IP."
fi

section "[4] Listening TCP services"
listen_tcp="$(sudo ss -ltnp 2>/dev/null)"
echo "$listen_tcp"

bad_listener_lines="$(echo "$listen_tcp" | tail -n +2 | grep -Ev '127\.0\.0\.1:|\[::ffff:127\.0\.0\.1\]:|\[::1\]:|::1:' || true)"
if [[ -n "${bad_listener_lines:-}" ]]; then
  warn "Non-loopback TCP listeners detected:"
  echo "$bad_listener_lines"
else
  ok "Only loopback TCP listeners detected."
fi

section "[5] Listening UDP services"
listen_udp="$(sudo ss -lunp 2>/dev/null)"
echo "$listen_udp"

udp_lines="$(echo "$listen_udp" | tail -n +2 || true)"
if [[ -n "${udp_lines// /}" ]]; then
  warn "UDP listeners detected. Review if expected."
else
  ok "No UDP listeners detected."
fi

section "[6] Firewall status"
ufw_status="$(sudo ufw status verbose 2>/dev/null || true)"
echo "$ufw_status"

if echo "$ufw_status" | grep -q "Status: active"; then
  ok "UFW is active."
else
  fail "UFW is NOT active."
fi

if echo "$ufw_status" | grep -q "Default: deny (incoming)"; then
  ok "Incoming default policy is deny."
else
  fail "Incoming default policy is not deny."
fi

section "[7] Established connections"
estab="$(sudo ss -tpn state established 2>/dev/null)"
echo "$estab"

suspect_estab="$(echo "$estab" | tail -n +2 | grep -v '127.0.0.1' | grep -v 'users:(("tor"' || true)"
if [[ -n "${suspect_estab:-}" ]]; then
  warn "Non-loopback established connections not owned by tor detected:"
  echo "$suspect_estab"
else
  ok "Established non-loopback connections appear tor-owned only."
fi

section "[8] Local self-scan"
if [[ -n "${lan_ip:-}" ]]; then
  scan_out="$(nmap -sS -Pn --top-ports 1000 "$lan_ip" 2>/dev/null || true)"
  echo "$scan_out"

  if echo "$scan_out" | grep -qE '^[0-9]+/tcp[[:space:]]+open'; then
    fail "Open ports detected in self-scan."
  elif echo "$scan_out" | grep -q "filtered"; then
    ok "Self-scan shows filtered ports / no exposed top-1000 TCP surface."
  else
    warn "Self-scan result was inconclusive."
  fi
else
  warn "Skipping self-scan because LAN IP was not detected."
fi

section "[9] Loopback service check"
loop_scan="$(nmap -Pn -sT 127.0.0.1 -p 8080,9050,9150,9151,37439,41451,45065 2>/dev/null || true)"
echo "$loop_scan"

section "[10] Kernel/UFW block hints"
dmesg_hits="$(sudo dmesg 2>/dev/null | grep -i -E 'ufw|block|reject|drop' | tail -n 20 || true)"
if [[ -n "${dmesg_hits:-}" ]]; then
  info "Recent firewall/kernel block messages:"
  echo "$dmesg_hits"
else
  info "No recent block messages found in dmesg tail."
fi

section "[FINAL VERDICT]"
if (( fail_count == 0 && warn_count == 0 )); then
  echo -e "${GREEN}[FINAL] CLEAN${NC}"
  echo "[STATUS] READY"
  echo "[MODE] Ghost mode ON. 👻"
elif (( fail_count == 0 && warn_count > 0 )); then
  echo -e "${YELLOW}[FINAL] STABLE WITH WARNINGS${NC}"
  echo "[STATUS] READY, BUT REVIEW WARNINGS"
  echo "[MODE] Ghost mode ON. 👻"
else
  echo -e "${RED}[FINAL] ACTION NEEDED${NC}"
  echo "[STATUS] NOT CLEAN"
  echo "[MODE] Ghost mode COMPROMISED / NEEDS REVIEW"
fi

echo
echo "Summary: FAIL=$fail_count WARN=$warn_count"
echo "IP is a shadow, presence is an illusion. 🕶️"
