# FANTOM_GHOST — GEO Command Center (beta snapshot)

User-space, single GEO Tor instance with loopback SOCKS `127.0.0.1:9250`.
These are **snapshots of the installed working Kali scripts**, not automatic
system installers. No `proplus-start` modifications are included.

## Existing commands

- `proplus-start` — existing, independent Tor Browser launch (not part of this snapshot)
- `ghost jp` — verify current Japan policy or select it, then launch isolated GEO Firefox
- `ghost de` / `ghost us` — country switching (requires close GEO Firefox first)
- `ghost browser` / `ghost status` / `ghost verify` / `ghost doctor`
- `ghost qa` — QA preflight; `ghost qa run` — live DE→US→JP testing (restarts GEO Tor 9250)

## Deployment details

The tools call each other from `~/.local/bin/`. `ghost qa` in this snapshot
expects `~/Загрузки/proplus-geo-switch-qa` (the existing tested location).
For reproducible installation, deploy **reviewed** snapshot files intentionally
and resolve the QA runner path separately. This Git snapshot does not alter
any live executable, profiles, system services, or the firewall.

## Verified from user-provided terminal output (2026-10-12)

- Japan exit and Tor confirmed; country verified in earlier browser tests.
- F9 automated: 14 PASS / 1 WARN / 0 FAIL; subsequent manual UFW status active.
- Phase 1L product repo clean before this release preparation.
- Country switching Germany: observed DE expected vs US returned by controller;
  switching QA **REVIEW_REQUIRED**. Controller rollback recovered Japan.
- `torrc` exact restore and Git unchanged after failed switch.
- `ghost` install successful; `ghost doctor` Tor connectivity PASS.

## OPEN acceptance gates

- Germany GeoIP mismatch root cause and Germany/USA switch regression.
- Browser DNS/IPv6 review; WebRTC result from earlier smoke test only.
- OpenSSL compiled/runtime mismatch warning evaluation.
- Full restore drill, cross-host reproducible deployment, and F9 FINAL CLOSED.

**Do not claim all-country support or guaranteed anonymity.** Ordinary Firefox
with SOCKS is not Tor Browser. Website account login can still identify a user.
A Git commit/push records audited source; it is not a security certification.

## License

No software license is granted by this snapshot. A `LICENSE` must be chosen
by the copyright holder and added in a separately reviewed change. No license
was silently assigned by this release script.
