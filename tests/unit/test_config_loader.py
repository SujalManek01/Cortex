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


def test_config_loader_loads_sprint004_configs(tmp_path: Path):
    # Setup mock files for Sprint 004
    grammar_data = {
        "version": "1.0",
        "connectors": ["and", "&", ","],
        "sequences": ["then", "after", "afterwards"]
    }
    rules_data = {
        "version": "1.0",
        "duplicate_action": "warning",
        "contradictory_action": "warning",
        "redundant_action": "information"
    }
    aliases_data = {
        "version": "1.0",
        "verbs": {
            "launch": "open",
            "run": "open"
        },
        "applications": {
            "vs code": "vscode"
        },
        "folders": {},
        "websites": {}
    }

    # Write to tmp directory
    (tmp_path / "apps.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "folders.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "websites.json").write_text(json.dumps({}), encoding="utf-8")
    (tmp_path / "grammar.json").write_text(json.dumps(grammar_data), encoding="utf-8")
    (tmp_path / "planner_rules.json").write_text(json.dumps(rules_data), encoding="utf-8")
    (tmp_path / "planner_aliases.json").write_text(json.dumps(aliases_data), encoding="utf-8")

    loader = ConfigLoader(tmp_path)
    config = loader.load()

    assert config.grammar is not None
    assert config.grammar.connectors == ("and", "&", ",")
    assert config.grammar.sequences == ("then", "after", "afterwards")

    assert config.planner_rules is not None
    assert config.planner_rules.duplicate_action == "warning"
    assert config.planner_rules.redundant_action == "information"

    assert config.planner_aliases is not None
    assert config.planner_aliases.verbs["launch"] == "open"
    assert config.planner_aliases.applications["vs code"] == "vscode"

