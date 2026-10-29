# Harrier

Attack surface reconnaissance and asset discovery platform. Harrier maps internet-facing assets associated with a target, including domains, IPs, ports, services, web sites, fingerprints and screenshots, and hunts for weaknesses using PoC plugins (NPoC/xing) and nuclei.

## 1# Notes

- Harrier is an attack surface reconnaissance and asset discovery platform for mapping internet-facing assets and hunting for weaknesses.
- Default credentials after a fresh install: `admin` / `harrier123`. Change the password in the UI after first login.
- The Docker quick-start path uses a prebuilt image and mounts this repository's `app/` and `docker/frontend/` source into the containers.
- **Self-update**: the bottom-right "Nuclei · Update" widget (or `POST /api/update/nuclei/`) downloads the latest nuclei engine and templates on the worker. To make an update survive `docker compose down` or container recreation, commit it afterwards: `docker commit harrier_worker harrier:latest`.
- Building a self-contained image from source requires the NPoC plugin repository and GeoLite2 databases, which are not vendored here. The prebuilt image is the supported path for now.
- The UI is English-only. The bundled frontend's built-in Chinese strings are translated at runtime.
- Licence: MIT. See `LICENSE`.

### 1.1 How to install Harrier

**Quick start (Docker)**

```bash
cd docker
docker volume create harrier_db
docker compose up -d
```

Then open `https://<host>:5003` and log in with `admin` / `harrier123` (change it in the UI after first login).

The compose stack uses a prebuilt image and mounts this repository's `app/` and `docker/frontend/` source into the containers, so code changes go live with:

```bash
docker compose restart web worker scheduler
```

**Repository layout**

- `app/`: Flask backend (API in `app/routes/`, task engine in `app/tasks/`, scanners in `app/services/`)
- `docker/`: compose stack, frontend bundle, nginx config, worker Dockerfiles
- `misc/`: systemd units and standalone (non-Docker) setup scripts
- `harrier_tool/`: auxiliary tools (GitHub leak, file leak)
- `test/`: test scripts

### 1.2 Feedback

Please use the repository issue tracker for bug reports and feature requests. Include deployment details (Docker or standalone), relevant logs, and reproduction steps where possible.

### 1.3 Many thanks for the Stars

Stars are appreciated. If Harrier is useful to you, please consider starring the repository.

## 2# Introduction

Harrier maps internet-facing assets associated with a target, including domains, IPs, ports, services, web sites, fingerprints and screenshots, and hunts for weaknesses using PoC plugins (NPoC/xing) and nuclei.

Before you start using it, please read and agree to the terms in `LICENSE` and `LICENSE.md`.

## 3# Features

1. Domain and IP reconnaissance tasks with configurable options (port scan, service/OS detection, site identification, screenshots, spider, file leak, nuclei, WIH, host collision)
2. Policy-based task dispatch: build a policy once (domain/IP config, site and risk config, PoC and weak-password brute-force config) and dispatch it against any target
3. Asset grouping, monitoring tasks, and scheduled (cron/interval) tasks
4. GitHub leak monitoring, FOFA task dispatch, fingerprint management
5. English-only UI (the bundled frontend's built-in Chinese strings are translated at runtime)

## 4# System requirements

The quick-start path requires Docker and Docker Compose. For source-based development, use the repository layout above. Windows is not covered by the quick-start path.

## 5# Screenshots

Screenshots are not currently bundled in this repository. If you add them, place them under `image/` and reference them here, for example:

- Login page
  <img width="1907" height="933" alt="image" src="https://github.com/user-attachments/assets/faae5eed-7d09-4a8f-88d8-41698914d76e" />


- Task page
  <img width="1920" height="970" alt="image" src="https://github.com/user-attachments/assets/2bf4edae-950a-4844-a006-1c710d6cdd68" />


- Site page
  <img width="1920" height="970" alt="image" src="https://github.com/user-attachments/assets/aa10f27d-c17f-4bb9-816e-4b576e8e556d" />



  
- Asset monitoring page


- Policy page
- Scheduled tasks
- GitHub monitoring task

## 6# Task option descriptions

| No. | Option | Description |
| --- | ------ | ----------- |
| 1 | Task name | Name of the reconnaissance task |
| 2 | Task target | Target(s) to reconnoitre; supports IP, IP range and domain, and multiple targets can be dispatched at once |
| 3 | Port scan | Enable port scanning |
| 4 | Service/OS detection | Identify services and operating systems; firewall interception may produce empty results |
| 5 | Site identification | Fingerprint web sites |
| 6 | Screenshots | Capture screenshots of site home pages |
| 7 | Spider | Crawl sites for URLs |
| 8 | File leak | Detect file-leak risks; may be intercepted by WAF |
| 9 | nuclei | Run nuclei PoCs against alive web sites; may be intercepted by WAF |
| 10 | WIH | Use WebInfoHunter to collect domains, AK/SK and other information from JavaScript |
| 11 | Host collision | Detect improper vhost configuration |
| 12 | Policy dispatch | Build a policy once and dispatch it against any target |

## 7# Configuration parameter descriptions

| Configuration | Description |
| ------------- | ----------- |
| Default credentials | `admin` / `harrier123`; change in the UI after first login |
| Docker compose | `cd docker && docker volume create harrier_db && docker compose up -d` |
| Source mounts | Compose mounts `app/` and `docker/frontend/`; restart `web worker scheduler` after code changes |
| Nuclei self-update | Bottom-right "Nuclei · Update" widget or `POST /api/update/nuclei/`; commit with `docker commit harrier_worker harrier:latest` to survive recreation |
| Image build | Requires the NPoC plugin repository and GeoLite2 databases; not vendored; the prebuilt image is the supported path for now |
| UI language | English-only; bundled frontend Chinese strings are translated at runtime |
| Licence | MIT. See `LICENSE` |

## 8# Forgotten password reset

No built-in password-reset command is documented in this README. Change the default password in the UI after first login. If you are locked out, use the deployment's database tooling or restore from a backup. Recreating the Docker volume will delete data.

