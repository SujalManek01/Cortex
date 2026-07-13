"""Integration tests: Sprint 002 metadata API endpoints.

Tests the full HTTP request → response pipeline for:
  GET /applications
  GET /folders
  GET /websites
  GET /capabilities

All tests use the ASGI test client against the real FastAPI app.
"""
from __future__ import annotations

from httpx import AsyncClient


# ── GET /applications ──────────────────────────────────────────────────────────

class TestApplicationsEndpoint:
    async def test_returns_200(self, http_client: AsyncClient):
        response = await http_client.get("/applications")
        assert response.status_code == 200

    async def test_response_has_applications_list(self, http_client: AsyncClient):
        response = await http_client.get("/applications")
        data = response.json()
        assert "applications" in data
        assert isinstance(data["applications"], list)

    async def test_application_items_have_required_fields(self, http_client: AsyncClient):
        response = await http_client.get("/applications")
        data = response.json()
        if data["applications"]:
            app = data["applications"][0]
            assert "alias" in app
            assert "name" in app


# ── GET /folders ───────────────────────────────────────────────────────────────

class TestFoldersEndpoint:
    async def test_returns_200(self, http_client: AsyncClient):
        response = await http_client.get("/folders")
        assert response.status_code == 200

    async def test_response_has_folders_list(self, http_client: AsyncClient):
        response = await http_client.get("/folders")
        data = response.json()
        assert "folders" in data
        assert isinstance(data["folders"], list)

    async def test_folder_items_have_required_fields(self, http_client: AsyncClient):
        response = await http_client.get("/folders")
        data = response.json()
        if data["folders"]:
            folder = data["folders"][0]
            assert "alias" in folder
            assert "path" in folder


# ── GET /websites ──────────────────────────────────────────────────────────────

class TestWebsitesEndpoint:
    async def test_returns_200(self, http_client: AsyncClient):
        response = await http_client.get("/websites")
        assert response.status_code == 200

    async def test_response_has_websites_list(self, http_client: AsyncClient):
        response = await http_client.get("/websites")
        data = response.json()
        assert "websites" in data
        assert isinstance(data["websites"], list)


# ── GET /capabilities ─────────────────────────────────────────────────────────

class TestCapabilitiesEndpoint:
    async def test_returns_200(self, http_client: AsyncClient):
        response = await http_client.get("/capabilities")
        assert response.status_code == 200

    async def test_response_has_capabilities_list(self, http_client: AsyncClient):
        response = await http_client.get("/capabilities")
        data = response.json()
        assert "capabilities" in data
        assert isinstance(data["capabilities"], list)

    async def test_all_sprint2_capabilities_present(self, http_client: AsyncClient):
        response = await http_client.get("/capabilities")
        data = response.json()
        capabilities = data["capabilities"]
        assert "application.open" in capabilities
        assert "application.close" in capabilities
        assert "folder.open" in capabilities
        assert "website.open" in capabilities
