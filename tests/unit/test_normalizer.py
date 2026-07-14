"""Unit tests: Normalizer — Sprint 003."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.planner.normalizer import Normalizer
from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.planner.tokenizer import Token, TokenType

# ── Fixtures ──────────────────────────────────────────────────────────────────

_CONFIG_DIR = Path(__file__).parents[2] / "config"


@pytest.fixture
def normalizer() -> Normalizer:
    return Normalizer(config_dir=_CONFIG_DIR)


def _words(*values: str) -> list[Token]:
    """Convenience: create a list of WORD tokens."""
    return [Token(type=TokenType.WORD, value=v) for v in values]


def _connector(value: str = "and") -> Token:
    return Token(type=TokenType.CONNECTOR, value=value)


# ── Connector normalisation ────────────────────────────────────────────────────

class TestConnectorNormalization:
    def test_and_becomes_then(self, normalizer):
        tokens = [*_words("open", "chrome"), _connector("and"), *_words("github")]
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome", "then", "github"]

    def test_ampersand_becomes_then(self, normalizer):
        tokens = [*_words("open", "chrome"), _connector("&"), *_words("github")]
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome", "then", "github"]

    def test_comma_becomes_then(self, normalizer):
        tokens = [*_words("open", "chrome"), _connector(","), *_words("github")]
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome", "then", "github"]

    def test_then_stays_then(self, normalizer):
        tokens = [*_words("open", "chrome"), _connector("then"), *_words("github")]
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome", "then", "github"]


# ── Verb alias expansion ──────────────────────────────────────────────────────

class TestVerbAliases:
    def test_launch_becomes_open(self, normalizer):
        tokens = _words("launch", "chrome")
        result = normalizer.normalize(tokens)
        assert result[0] == "open"

    def test_run_becomes_open(self, normalizer):
        tokens = _words("run", "chrome")
        result = normalizer.normalize(tokens)
        assert result[0] == "open"

    def test_start_becomes_open(self, normalizer):
        tokens = _words("start", "chrome")
        result = normalizer.normalize(tokens)
        assert result[0] == "open"

    def test_quit_becomes_close(self, normalizer):
        tokens = _words("quit", "chrome")
        result = normalizer.normalize(tokens)
        assert result[0] == "close"

    def test_exit_becomes_close(self, normalizer):
        tokens = _words("exit", "chrome")
        result = normalizer.normalize(tokens)
        assert result[0] == "close"


# ── Application multi-word alias expansion ────────────────────────────────────

class TestApplicationAliases:
    def test_vs_code_becomes_vscode(self, normalizer):
        tokens = _words("open", "vs", "code")
        result = normalizer.normalize(tokens)
        assert result == ["open", "vscode"]

    def test_visual_studio_code_becomes_vscode(self, normalizer):
        tokens = _words("open", "visual", "studio", "code")
        result = normalizer.normalize(tokens)
        assert result == ["open", "vscode"]

    def test_google_chrome_becomes_chrome(self, normalizer):
        tokens = _words("open", "google", "chrome")
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome"]


# ── Website multi-word alias expansion ────────────────────────────────────────

class TestWebsiteAliases:
    def test_chat_gpt_becomes_chatgpt(self, normalizer):
        tokens = _words("open", "chat", "gpt")
        result = normalizer.normalize(tokens)
        assert result == ["open", "chatgpt"]

    def test_git_hub_becomes_github(self, normalizer):
        tokens = _words("open", "git", "hub")
        result = normalizer.normalize(tokens)
        assert result == ["open", "github"]


# ── Folder multi-word alias expansion ─────────────────────────────────────────

class TestFolderAliases:
    def test_my_downloads_becomes_downloads(self, normalizer):
        tokens = _words("open", "my", "downloads")
        result = normalizer.normalize(tokens)
        assert result == ["open", "downloads"]

    def test_downloads_folder_becomes_downloads(self, normalizer):
        tokens = _words("open", "downloads", "folder")
        result = normalizer.normalize(tokens)
        assert result == ["open", "downloads"]


# ── Greedy longest-match ──────────────────────────────────────────────────────

class TestGreedyMatch:
    def test_longest_alias_wins(self, normalizer):
        """'visual studio code' (3-word) should beat 'visual studio' (2-word)."""
        tokens = _words("open", "visual", "studio", "code")
        result = normalizer.normalize(tokens)
        assert result == ["open", "vscode"]


# ── No alias: passthrough ─────────────────────────────────────────────────────

class TestPassthrough:
    def test_known_word_without_alias_passed_through(self, normalizer):
        tokens = _words("open", "chrome")
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome"]

    def test_unknown_word_passed_through(self, normalizer):
        """Normalizer does not reject unknown words; that is Target Resolver's job."""
        tokens = _words("open", "abcxyz123")
        result = normalizer.normalize(tokens)
        assert result == ["open", "abcxyz123"]


# ── Full sentence normalisation ────────────────────────────────────────────────

class TestFullSentence:
    def test_open_google_chrome_and_vs_code(self, normalizer):
        tokens = [
            *_words("open", "google", "chrome"),
            _connector("and"),
            *_words("vs", "code"),
        ]
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome", "then", "vscode"]

    def test_launch_chrome_then_github(self, normalizer):
        tokens = [*_words("launch", "chrome"), _connector("then"), *_words("github")]
        result = normalizer.normalize(tokens)
        assert result == ["open", "chrome", "then", "github"]


# ── Error handling ─────────────────────────────────────────────────────────────

class TestErrors:
    def test_empty_token_list_raises(self, normalizer):
        with pytest.raises(PlanningError) as exc:
            normalizer.normalize([])
        assert exc.value.error_code == PlannerErrorCode.NORMALIZATION_ERROR

    def test_missing_config_dir_raises(self, tmp_path):
        """Normalizer raises PlanningError at construction if aliases file is missing."""
        with pytest.raises(PlanningError) as exc:
            Normalizer(config_dir=tmp_path)
        assert exc.value.error_code == PlannerErrorCode.NORMALIZATION_ERROR

    def test_invalid_json_raises(self, tmp_path):
        """Normalizer raises PlanningError at construction if aliases file is invalid JSON."""
        (tmp_path / "planner_aliases.json").write_text("{invalid json}", encoding="utf-8")
        with pytest.raises(PlanningError) as exc:
            Normalizer(config_dir=tmp_path)
        assert exc.value.error_code == PlannerErrorCode.NORMALIZATION_ERROR
