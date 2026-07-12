"""Auto-discovery of common Windows application installations.

Refinement 3: Attempt automatic detection before falling back to apps.json.

Discovery scans a curated list of known installation paths in order of
preference. Only the first found candidate per application is used.
The ConfigLoader merges these results with apps.json (apps.json wins on conflict).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_USERNAME: str = os.environ.get("USERNAME", os.environ.get("COMPUTERNAME", "user"))


def _resolve(path_template: str) -> str:
    """Substitute {username} placeholder with the current Windows username."""
    return path_template.replace("{username}", _USERNAME)


@dataclass(frozen=True)
class DiscoveredApp:
    """A concrete application installation found on this system."""

    name: str
    alias: str
    executable: str
    path: str


# ── Known application specifications ──────────────────────────────────────────
# Each entry lists candidate absolute paths tried in order of preference.
# {username} is resolved at runtime via _resolve().

_KNOWN_APPS: list[dict] = [
    {
        "name": "VS Code",
        "alias": "vscode",
        "executable": "Code.exe",
        "candidates": [
            r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            r"C:\Program Files (x86)\Microsoft VS Code\Code.exe",
        ],
    },
    {
        "name": "Google Chrome",
        "alias": "chrome",
        "executable": "chrome.exe",
        "candidates": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{username}\AppData\Local\Google\Chrome\Application\chrome.exe",
        ],
    },
    {
        "name": "Microsoft Edge",
        "alias": "edge",
        "executable": "msedge.exe",
        "candidates": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ],
    },
    {
        "name": "Mozilla Firefox",
        "alias": "firefox",
        "executable": "firefox.exe",
        "candidates": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            r"C:\Users\{username}\AppData\Local\Mozilla Firefox\firefox.exe",
        ],
    },
    {
        "name": "Notepad",
        "alias": "notepad",
        "executable": "notepad.exe",
        "candidates": [
            r"C:\Windows\System32\notepad.exe",
            r"C:\Windows\notepad.exe",
        ],
    },
    {
        "name": "File Explorer",
        "alias": "explorer",
        "executable": "explorer.exe",
        "candidates": [
            r"C:\Windows\explorer.exe",
        ],
    },
    {
        "name": "Calculator",
        "alias": "calculator",
        "executable": "calc.exe",
        "candidates": [
            r"C:\Windows\System32\calc.exe",
        ],
    },
    {
        "name": "Paint",
        "alias": "paint",
        "executable": "mspaint.exe",
        "candidates": [
            r"C:\Windows\System32\mspaint.exe",
        ],
    },
    {
        "name": "Task Manager",
        "alias": "taskmgr",
        "executable": "Taskmgr.exe",
        "candidates": [
            r"C:\Windows\System32\Taskmgr.exe",
        ],
    },
    {
        "name": "Windows Terminal",
        "alias": "terminal",
        "executable": "wt.exe",
        "candidates": [
            r"C:\Users\{username}\AppData\Local\Microsoft\WindowsApps\wt.exe",
        ],
    },
    {
        "name": "Spotify",
        "alias": "spotify",
        "executable": "Spotify.exe",
        "candidates": [
            r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
            r"C:\Program Files\Spotify\Spotify.exe",
        ],
    },
    {
        "name": "Slack",
        "alias": "slack",
        "executable": "slack.exe",
        "candidates": [
            r"C:\Users\{username}\AppData\Local\slack\slack.exe",
        ],
    },
    {
        "name": "Discord",
        "alias": "discord",
        "executable": "Discord.exe",
        "candidates": [
            r"C:\Users\{username}\AppData\Local\Discord\Update.exe",
            r"C:\Users\{username}\AppData\Roaming\Discord\Discord.exe",
        ],
    },
]


def discover_installed_apps() -> list[DiscoveredApp]:
    """Scan known installation paths and return apps confirmed to exist on disk.

    Only the first matching candidate path per application is used.
    Applications not found on disk are omitted from the result.

    Returns:
        List of DiscoveredApp instances for all found applications.
    """
    discovered: list[DiscoveredApp] = []

    for spec in _KNOWN_APPS:
        for candidate_template in spec["candidates"]:
            resolved = _resolve(candidate_template)
            if Path(resolved).exists():
                discovered.append(
                    DiscoveredApp(
                        name=spec["name"],
                        alias=spec["alias"],
                        executable=spec["executable"],
                        path=resolved,
                    )
                )
                break  # Stop at first found candidate for this app.

    return discovered
