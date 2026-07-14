"""Unit tests: ConfigLoader.

Verifies that ConfigLoader correctly parses versioned config files
for applications, folders, and websites under the Sprint 002 schema,
and supports username placeholder resolution.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.config.config_loader import ConfigLoader, AppEntry


def test_config_loader_loads_versioned_schemas(tmp_path: Path):
    # 1. Setup mock config files using Sprint 002 versioned schema format
    apps_data = {
        "version": "1.0",
        "entries": [
            {
                "name": "Mock App",
                "alias": "mockapp",
                "executable": "mockapp.exe",
                "path": "C:\\Program Files\\MockApp\\mockapp.exe"
            }
        ]
    }
    
    folders_data = {
        "version": "1.0",
        "entries": [
            {
                "alias": "mock_desktop",
                "path": "C:\\Users\\{username}\\Desktop"
            }
        ]
    }
    
    websites_data = {
        "version": "1.0",
        "entries": [
            {
                "alias": "mock_site",
                "url": "https://example.mock"
            }
        ]
    }
    
    # Write to tmp directory
    (tmp_path / "apps.json").write_text(json.dumps(apps_data), encoding="utf-8")
    (tmp_path / "folders.json").write_text(json.dumps(folders_data), encoding="utf-8")
    (tmp_path / "websites.json").write_text(json.dumps(websites_data), encoding="utf-8")
    
    # 2. Instantiate and run ConfigLoader
    loader = ConfigLoader(tmp_path)
    config = loader.load()
    
    # 3. Assertions
    # Verify app loaded (might have other auto-discovered apps, so check that our mockapp is present)
    mock_app = config.get_app("mockapp")
    assert mock_app is not None
    assert mock_app.name == "Mock App"
    assert mock_app.path == "C:\\Program Files\\MockApp\\mockapp.exe"
    
    # Verify folder loaded and username resolved
    resolved_path = config.get_alias("mock_desktop")
    assert resolved_path is not None
    assert "{username}" not in resolved_path
    assert "mock_desktop" in config.all_aliases
    
    # Verify website loaded
    website_url = config.get_website("mock_site")
    assert website_url == "https://example.mock"
    assert "mock_site" in config.all_websites
