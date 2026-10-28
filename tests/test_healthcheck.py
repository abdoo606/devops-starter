from __future__ import annotations

import json
import socket
import threading

import pytest

from devops.healthcheck import Check, HealthReport, disk_check, main, memory_check, tcp_check


def test_report_json_shape():
    report = HealthReport().add(Check("a", True, "fine", 1.23))
    payload = json.loads(report.to_json())
    assert payload["status"] == "ok"
    assert payload["checks"][0]["duration_ms"] == 1.23


def test_report_fails_if_any_check_fails():
    report = HealthReport().add(Check("a", True)).add(Check("b", False, "boom"))
    assert report.healthy is False
    assert json.loads(report.to_json())["status"] == "fail"


def test_disk_check_on_existing_path(tmp_path):
    check = disk_check(str(tmp_path), min_free_mb=1)
    assert check.passed and "MB free" in check.detail


def test_disk_check_with_impossible_threshold(tmp_path):
    assert disk_check(str(tmp_path), min_free_mb=10**9).passed is False


def test_disk_check_missing_path():
    assert disk_check("/definitely/not/here").passed is False


def test_memory_check_on_missing_proc_file():
    assert memory_check("/definitely/not/here").passed is False


def test_tcp_check_against_a_real_listener():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    port = server.getsockname()[1]
    try:
        assert tcp_check("127.0.0.1", port, timeout=2).passed
    finally:
        server.close()


def test_tcp_check_fails_on_closed_port():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()  # port is now free, so connect must fail quickly
    assert tcp_check("127.0.0.1", port, timeout=0.2).passed is False


def test_cli_exit_codes(tmp_path, capsys):
    assert main(["--disk", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "ok"
    assert main(["--disk", "/definitely/not/here"]) == 1


def test_cli_noop_human_output(capsys):
    assert main([]) == 0
    assert "healthy" in capsys.readouterr().out
