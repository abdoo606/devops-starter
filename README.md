# 30 · devops

Container health checks, Dockerfile and CI for a Python service.

## Run

```bash
python -m devops.healthcheck --disk / --json
```

## Test

```bash
pytest projects/30-devops-starter -q
```

## What it demonstrates

- A healthcheck binary for Docker `HEALTHCHECK` and Kubernetes probes
- TCP, disk and memory checks with timings and machine-readable JSON
- Correct exit codes: 0 healthy, 1 unhealthy
- Multi-stage Dockerfile and a compose file with a real healthcheck
