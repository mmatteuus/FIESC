from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def wait_for(url: str, timeout: float = 30) -> httpx.Response:
    deadline = time.monotonic() + timeout
    error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=2)
            response.raise_for_status()
            return response
        except Exception as exc:
            error = exc
            time.sleep(0.5)
    raise RuntimeError(f"Servidor nao respondeu em {url}: {error}")


def stop(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def validate_api() -> dict[str, object]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "fiesc_pm.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8010",
            "--log-level",
            "warning",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    try:
        health = wait_for("http://127.0.0.1:8010/health").json()
        ready = httpx.get("http://127.0.0.1:8010/ready", timeout=15).json()
        model = httpx.get("http://127.0.0.1:8010/model-info", timeout=15).json()
        demos = json.loads(
            (ROOT / "data" / "demo" / "demo_events.json").read_text(encoding="utf-8")
        )
        payload = {
            "event": demos[0]["event"],
            "question": "Quais verificacoes devo priorizar?",
            "provider": "extractive",
            "top_k": 3,
        }
        recommendation = httpx.post(
            "http://127.0.0.1:8010/v1/recommendations", json=payload, timeout=30
        ).json()
        return {
            "health": health["status"],
            "ready": ready["status"],
            "model": model["version"],
            "knowledge_chunks": ready["knowledge_chunks"],
            "recommendation_status": recommendation["status"],
            "fault": recommendation["predicted_fault"],
            "citations": len(recommendation["citations"]),
            "provider": recommendation["provider"],
            "latency_ms": recommendation["latency_ms"],
        }
    finally:
        stop(process)


def validate_streamlit() -> dict[str, object]:
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app/streamlit_app.py",
            "--server.address=127.0.0.1",
            "--server.port=8510",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=NO_WINDOW,
    )
    try:
        health = wait_for("http://127.0.0.1:8510/_stcore/health")
        page = httpx.get("http://127.0.0.1:8510", timeout=10)
        page.raise_for_status()
        return {
            "health": health.text.strip(),
            "http_status": page.status_code,
            "shell_loaded": "Streamlit" in page.text,
        }
    finally:
        stop(process)


def main() -> None:
    print(json.dumps({"api": validate_api(), "streamlit": validate_streamlit()}, indent=2))


if __name__ == "__main__":
    main()
