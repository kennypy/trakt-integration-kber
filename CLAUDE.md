# Notes for Claude

## kennypy's homelab (Proxmox node `pve`)

- **Network bridge is `vmbr1`** (192.168.1.0/24 LAN). `vmbr2` is 10.99.0.1/24.
  **`vmbr0` does NOT exist — never use the default bridge; always pass `bridge=vmbr1`**
  when creating VMs/containers via Clustr.
- HAOS VM 100 (Home Assistant; config packages at
  `/mnt/data/supervisor/homeassistant/packages/`, guest agent available).
- arr-stack LXC 145 at 192.168.1.125 — Docker host for the media pipeline
  (compose at `/opt/arr`): Sonarr :8989, Radarr :7878, Prowlarr :9696,
  Bazarr :6767, SABnzbd :8080, Jellyseerr :5055, plus Yamtrack :8000
  (separate compose project at `/opt/yamtrack`).
- Jellyfin LXC 107 at 192.168.1.243 (:8096), native install, user `kenjelly`.
- Docker-in-LXC is the established pattern (145); Clustr's `create_container`
  cannot set the `nesting` feature, so prefer deploying Docker services onto 145.
- LXC 146 (`yamtrack`) is an unused, unbootable leftover (wrong bridge) —
  safe to delete when kennypy confirms.

## This repository

- Fork of `dylandoamaral/trakt-integration`, personalized for kennypy.
- Trakt put API apps behind a VIP paywall (2026), which killed the live
  integration; the HA config entry is kept in `setup_error` state intentionally.
  Replacement sensors live in HA package `media_tracking.yaml` (Jellyfin
  Next Up + Jellyseerr requests) plus native Sonarr/Radarr integrations.
- Workflow: develop on the designated `claude/...` branch, PR to `main`,
  merge after tests pass (`python -m pytest`, black + isort per Makefile).
