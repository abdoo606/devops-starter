"""A dependency-free healthcheck binary for container HEALTHCHECK / k8s probes."""

from __future__ import annotations

import json
import socket
import sys
import time
from dataclasses import dataclass, field


@dataclass(slots=True)
class Check:
    name: str
    passed: bool
    detail: str = ""
    duration_ms: float = 0.0


@dataclass(slots=True)
class HealthReport:
    checks: list[Check] = field(default_factory=list)

    def add(self, check: Check) -> "HealthReport":
        self.checks.append(check)
        return self

    @property
    def healthy(self) -> bool:
        return all(c.passed for c in self.checks)

    def to_json(self) -> str:
        return json.dumps(
            {
                "status": "ok" if self.healthy else "fail",
                "checks": [
                    {"name": c.name, "passed": c.passed, "detail": c.detail, "duration_ms": round(c.duration_ms, 2)}
                    for c in self.checks
                ],
            },
            indent=2,
        )


def tcp_check(host: str, port: int, *, timeout: float = 1.0) -> Check:
    start = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            passed, detail = True, "connected"
    except OSError as exc:
        passed, detail = False, str(exc)
    return Check(f"tcp:{host}:{port}", passed, detail, (time.perf_counter() - start) * 1000)


def disk_check(path: str, *, min_free_mb: int = 100) -> Check:
    import shutil

    start = time.perf_counter()
    try:
        usage = shutil.disk_usage(path)
        free_mb = usage.free / (1024 * 1024)
        passed = free_mb >= min_free_mb
        detail = f"{free_mb:.0f} MB free (min {min_free_mb})"
    except OSError as exc:
        passed, detail = False, str(exc)
    return Check(f"disk:{path}", passed, detail, (time.perf_counter() - start) * 1000)


def memory_check(path: str = "/proc/meminfo", *, min_free_mb: int = 50) -> Check:
    start = time.perf_counter()
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemAvailable:"):
                    free_mb = int(line.split()[1]) / 1024
                    return Check(
                        "memory", free_mb >= min_free_mb, f"{free_mb:.0f} MB available",
                        (time.perf_counter() - start) * 1000,
                    )
        return Check("memory", False, "MemAvailable not found", 0.0)
    except OSError as exc:
        return Check("memory", False, str(exc), (time.perf_counter() - start) * 1000)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run container health checks.")
    parser.add_argument("--tcp", help="host:port to connect to")
    parser.add_argument("--disk", help="path to check for free space")
    parser.add_argument("--min-free-mb", type=int, default=100)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = HealthReport()
    if args.tcp:
        host, _, port = args.tcp.partition(":")
        report.add(tcp_check(host or "127.0.0.1", int(port or 80)))
    if args.disk:
        report.add(disk_check(args.disk, min_free_mb=args.min_free_mb))
    if not report.checks:
        report.add(Check("noop", True, "nothing to check"))

    print(report.to_json() if args.json else ("healthy" if report.healthy else "unhealthy"))
    return 0 if report.healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
