"""Integration tests: POST /plan and POST /command — Sprint 003."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


# ── POST /plan ─────────────────────────────────────────────────────────────────

class TestPostPlan:
    @pytest.mark.asyncio
    async def test_plan_open_chrome(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "Open Chrome"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["planner"] == "rule_planner"
        assert body["confidence"] == 1.0
        assert body["step_count"] == 1
        assert len(body["steps"]) == 1
        assert body["steps"][0]["capability"] == "application.open"
        assert body["steps"][0]["target"] == "chrome"
        assert body["error"] is None

    @pytest.mark.asyncio
    async def test_plan_multi_step(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "Open Chrome and GitHub"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["step_count"] == 2
        caps = [s["capability"] for s in body["steps"]]
        assert "application.open" in caps
        assert "website.open" in caps

    @pytest.mark.asyncio
    async def test_plan_normalized_input_returned(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "OPEN  CHROME"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["normalized_input"] == "open chrome"

    @pytest.mark.asyncio
    async def test_plan_unknown_target_returns_200_with_failure(self, http_client: AsyncClient):
        """Planning errors return HTTP 200 with success=False (not an HTTP error)."""
        resp = await http_client.post("/plan", json={"command": "Open ABCXYZ123"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["error_code"] == "UNKNOWN_TARGET"
        assert body["step_count"] == 0

    @pytest.mark.asyncio
    async def test_plan_empty_command_rejected_by_schema(self, http_client: AsyncClient):
        """Empty string is rejected by CommandRequest schema (min_length=1)."""
        resp = await http_client.post("/plan", json={"command": ""})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_plan_missing_command_field_rejected(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_plan_verb_alias_expanded(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "Launch Chrome"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["steps"][0]["capability"] == "application.open"

    @pytest.mark.asyncio
    async def test_plan_warnings_for_duplicate(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "Open Chrome then open Chrome"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["warnings"]) > 0
        assert body["warnings"][0]["code"] == "DUPLICATE_ACTION"

    @pytest.mark.asyncio
    async def test_plan_planning_time_present(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "Open Chrome"})
        body = resp.json()
        assert "planning_time_ms" in body
        assert body["planning_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_plan_mixed_intents_succeeds(self, http_client: AsyncClient):
        resp = await http_client.post("/plan", json={"command": "Open Chrome then close Notepad"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["step_count"] == 2


# ── POST /command ──────────────────────────────────────────────────────────────

class TestPostCommand:
    @pytest.mark.asyncio
    async def test_command_planning_failure_returns_400(self, http_client: AsyncClient):
        """When planning fails, POST /command returns HTTP 400 (not 200)."""
        resp = await http_client.post("/command", json={"command": "Open ABCXYZ123"})
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error_code"] == "UNKNOWN_TARGET"

    @pytest.mark.asyncio
    async def test_command_empty_body_rejected(self, http_client: AsyncClient):
        resp = await http_client.post("/command", json={})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_command_mixed_intents_succeeds(self, http_client: AsyncClient):
        resp = await http_client.post("/command", json={"command": "Open Chrome then close Notepad"})
        assert resp.status_code == 200


# ── Backward compatibility: POST /execute still works ─────────────────────────

class TestExecuteBackwardCompat:
    @pytest.mark.asyncio
    async def test_execute_notepad_still_works(self, http_client: AsyncClient):
        payload = {
            "plan": {
                "steps": [
                    {"capability": "application.open", "target": "notepad"}
                ]
            }
        }
        resp = await http_client.post("/execute", json=payload)
        # Must be 200 — execution result may succeed or fail depending on environment
        assert resp.status_code == 200
        body = resp.json()
        assert "execution_id" in body
        assert "status" in body

    @pytest.mark.asyncio
    async def test_execute_unknown_app_returns_error(self, http_client: AsyncClient):
        payload = {
            "plan": {
                "steps": [
                    {"capability": "application.open", "target": "unknownapp999"}
                ]
            }
        }
        resp = await http_client.post("/execute", json=payload)
        # Safety policy should reject this
        assert resp.status_code in (400, 403)
