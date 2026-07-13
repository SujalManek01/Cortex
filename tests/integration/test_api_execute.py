"""Integration tests: API routes via ASGI test client.

Tests the full HTTP request → response pipeline:
  POST /execute happy path
  POST /execute validation failures (400)
  POST /execute safety violations (403)
  POST /execute concurrent execution (409)
  GET /status
  GET /health

All tests use mock executors to avoid OS side-effects.
The ASGI test client (httpx + ASGITransport) runs against the real FastAPI app
without starting a real server.
"""
from __future__ import annotations

import asyncio
from unittest.mock import patch

from httpx import AsyncClient



# ── Helpers ────────────────────────────────────────────────────────────────────

def _open_notepad_body() -> dict:
    """Minimal valid request body: open notepad (always safe/registered in test config)."""
    return {
        "version": "1.0",
        "plan": {
            "steps": [{"capability": "application.open", "target": "notepad"}],
        }
    }


# ── Health check ───────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    async def test_health_returns_200(self, http_client: AsyncClient):
        response = await http_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


# ── Status endpoint ────────────────────────────────────────────────────────────

class TestStatusEndpoint:
    async def test_status_idle_on_startup(self, http_client: AsyncClient):
        response = await http_client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["busy"] is False
        assert data["status"] == "idle"


# ── POST /execute happy path ───────────────────────────────────────────────────

class TestExecuteHappyPath:
    async def test_execute_returns_200(self, http_client: AsyncClient):
        """A valid request with a registered app should return 200 with state."""
        with patch("backend.executors.application_open.subprocess.Popen"):
            response = await http_client.post("/execute", json=_open_notepad_body())
        assert response.status_code == 200

    async def test_execute_response_has_plan_id(self, http_client: AsyncClient):
        with patch("backend.executors.application_open.subprocess.Popen"):
            response = await http_client.post("/execute", json=_open_notepad_body())
        data = response.json()
        assert "execution_id" in data
        assert data["execution_id"] is not None

    async def test_execute_response_status_completed(self, http_client: AsyncClient):
        with patch("backend.executors.application_open.subprocess.Popen"):
            response = await http_client.post("/execute", json=_open_notepad_body())
        data = response.json()
        assert data["status"] == "completed"

    async def test_execute_response_has_step_results(self, http_client: AsyncClient):
        with patch("backend.executors.application_open.subprocess.Popen"):
            response = await http_client.post("/execute", json=_open_notepad_body())
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "success"

    async def test_backend_generates_plan_id(self, http_client: AsyncClient):
        """Two identical requests must produce different plan IDs."""
        with patch("backend.executors.application_open.subprocess.Popen"):
            r1 = await http_client.post("/execute", json=_open_notepad_body())
            r2 = await http_client.post("/execute", json=_open_notepad_body())
        assert r1.json()["execution_id"] != r2.json()["execution_id"]


# ── POST /execute validation failures (400) ────────────────────────────────────

class TestExecuteValidationFailures:
    async def test_empty_steps_returns_400(self, http_client: AsyncClient):
        body = {"version": "1.0", "plan": {"steps": []}}
        response = await http_client.post("/execute", json=body)
        # Pydantic min_length=1 raises 422; our validator raises 400.
        assert response.status_code in (400, 422)

    async def test_unknown_action_returns_400(self, http_client: AsyncClient):
        body = {
            "version": "1.0",
            "plan": {"steps": [{"capability": "browser.open", "target": "https://x.com"}]},
        }
        response = await http_client.post("/execute", json=body)
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error_code"] == "validation_error"

    async def test_invalid_action_format_returns_400(self, http_client: AsyncClient):
        body = {
            "version": "1.0",
            "plan": {"steps": [{"capability": "openapp", "target": ""}]},
        }
        response = await http_client.post("/execute", json=body)
        assert response.status_code == 400


# ── POST /execute safety violations (403) ─────────────────────────────────────

class TestExecuteSafetyViolations:
    async def test_unregistered_app_returns_403(self, http_client: AsyncClient):
        body = {
            "version": "1.0",
            "plan": {"steps": [{"capability": "application.open", "target": "malicious_app"}]},
        }
        response = await http_client.post("/execute", json=body)
        assert response.status_code == 403
        data = response.json()
        assert data["detail"]["error_code"] == "safety_violation"

    async def test_raw_path_in_parameters_returns_403(self, http_client: AsyncClient):
        body = {
            "version": "1.0",
            "plan": {"steps": [{"capability": "application.open", "target": r"C:\Windows\cmd.exe"}]},
        }
        response = await http_client.post("/execute", json=body)
        assert response.status_code == 403

    async def test_unknown_alias_returns_403(self, http_client: AsyncClient):
        body = {
            "version": "1.0",
            "plan": {"steps": [{"capability": "folder.open", "target": "secret"}]},
        }
        response = await http_client.post("/execute", json=body)
        assert response.status_code == 403


# ── POST /execute concurrent execution (409) ───────────────────────────────────

class TestExecuteConcurrentExecution:
    async def test_concurrent_plan_returns_409(self, http_client: AsyncClient):
        """Sending a second request while first is processing must return 409."""
        from unittest.mock import patch

        async def slow_popen(*args, **kwargs):
            await asyncio.sleep(0.3)

        async def slow_to_thread(func, *args, **kwargs):
            await asyncio.sleep(0.3)

        with patch("backend.executors.application_open.asyncio.to_thread", slow_to_thread):
            task = asyncio.create_task(
                http_client.post("/execute", json=_open_notepad_body())
            )
            await asyncio.sleep(0.05)

            response2 = await http_client.post("/execute", json=_open_notepad_body())
            assert response2.status_code == 409
            data = response2.json()
            assert data["detail"]["error_code"] == "concurrent_execution"

            await task
