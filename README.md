# ObservaGuard – AI‑Powered K8s Drift & Secret‑Leak Sentinel

ObservaGuard is a recruiter‑ready, **complex yet runnable** platform that showcases **AI + DevOps + Kubernetes + Docker** skills in a single repo.  
It detects **Kubernetes configuration drift**, **unsafe changes in GitOps manifests**, and **accidental secret leaks**, with an **ML service** to flag anomalous deploy patterns.  
Run locally with **Docker Compose** or deploy to a cluster using **Helm**.

## Highlights
- **Microservices**: FastAPI backend, ML anomaly service, React + Vite dashboard, Go cluster agent.
- **AI**: Isolation Forest‑based anomaly scoring for deployment patterns and drift events.
- **Security**: Secret‑leak heuristics + regex + entropy checks on incoming YAML/JSON/commits.
- **DevOps**: Dockerfiles, docker‑compose, GitHub Actions CI, Helm chart, K8s manifests.
- **K8s**: Agent as a DaemonSet to stream metrics/log snippets; backend exposes metrics and Prometheus scrape config.
- **Doable**: Works out‑of‑the‑box via `docker compose up`. Helm chart values let you deploy to any K8s.

## Quick Start (Local)
```bash
# 1) Copy .env template
cp .env.example .env

# 2) Build & run
docker compose up --build

# 3) Open the UI
# http://localhost:5173
```

## Services
- **backend/** (FastAPI): API, drift/secret checks, auth (demo token), event store (SQLite), Prometheus metrics.
- **ml/** (FastAPI): IsolationForest model; simple train/score endpoints with persisted model.
- **agent/** (Go): K8s-node data collector (falls back to mock mode locally).
- **frontend/** (React + Vite + Tailwind): Dashboards & triage UI.

## Kubernetes
- **charts/observaguard** Helm chart (values, templates).
- **k8s/** raw manifests (for quick demo without Helm).

## CI/CD
- **.github/workflows/**: CI pipeline for lint, test, build, Docker, and Helm chart lint.

## Project Structure
```
ObservaGuard/
  backend/
  ml/
  agent/
  frontend/
  charts/observaguard/
  k8s/
  .github/workflows/
  docker-compose.yml
  .env.example
```

## Demo Tokens
- Use header `Authorization: Bearer devtoken` for local API calls.

## Notes
- This is intentionally feature‑rich but compact; each service has tests and health checks.
- The “agent” runs in **mock mode** when not inside K8s, so local dev still shows live data.
