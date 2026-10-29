# Harrier

Attack surface reconnaissance and asset discovery platform. Harrier maps internet-facing assets associated with a target — domains, IPs, ports, services, web sites, fingerprints, screenshots — and hunts for weaknesses using PoC plugins (NPoC/xing) and nuclei.

## Features

- Domain and IP reconnaissance tasks with configurable options (port scan, service/OS detection, site identification, screenshots, spider, file-leak, nuclei, WIH, host collision)
- Policy-based task dispatch: build a policy once (domain/IP config, site & risk config, PoC and weak-password brute config) and dispatch it against any target
- Asset grouping, monitoring tasks, and scheduled (cron/interval) tasks
- GitHub leak monitoring, FOFA task dispatch, fingerprint management
- English-only UI (the bundled frontend's built-in Chinese strings are translated at runtime)

## Quick start (Docker)

```bash
cd docker
docker volume create harrier_db
docker compose up -d
```

Then open `https://<host>:5003` and log in with `admin` / `harrier123` (change it in the UI after first login).

The compose stack uses a prebuilt image and mounts this repo's `app/` and `docker/frontend/` source into the containers, so code changes go live with:

```bash
docker compose restart web worker scheduler
```

## Repository layout

- `app/` — Flask backend (API in `app/routes/`, task engine in `app/tasks/`, scanners in `app/services/`)
- `docker/` — compose stack, frontend bundle, nginx config, worker Dockerfiles
- `misc/` — systemd units and standalone (non-Docker) setup scripts
- `harrier_tool/` — auxiliary tools (GitHub leak, file leak)
- `test/` — test scripts

## Notes

- Default credentials after a fresh install: `admin` / `harrier123`
- nuclei runs only against alive web sites with CVE-tag templates; zero hits on a target without matching templates is expected
- **Self-update**: the bottom-right "Nuclei · Update" widget (or `POST /api/update/nuclei/`) downloads the latest nuclei engine and templates on the worker. To make an update survive `docker compose down` / container recreation, commit it afterwards: `docker commit harrier_worker harrier:latest`
- Building a self-contained image from source requires the NPoC plugin repo and GeoLite2 databases, which are not vendored here; the prebuilt image is the supported path for now

## License

MIT — see `LICENSE` and `LICENSE.md`.
