#!/usr/bin/env bash
if [ -z "$1" ]; then
  echo "Օգտագործում՝ $0 <URL>"
  exit 1
fi
curl --socks5-hostname 127.0.0.1:9050 "$1"
