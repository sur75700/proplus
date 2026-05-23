#!/usr/bin/env bash
set -e

echo "== Tor service status =="
systemctl is-active --quiet tor@default && echo "tor@default: active" || echo "tor@default: NOT active"

echo
echo "== Normal IP =="
curl -s https://api.ipify.org || echo "failed"

echo
echo "== Tor IP (via SOCKS5 127.0.0.1:9050) =="
curl -s --socks5-hostname 127.0.0.1:9050 https://api.ipify.org || echo "failed"

echo
echo "Done."
