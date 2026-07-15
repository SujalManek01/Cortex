"""Unit tests: Tokenizer — Sprint 003."""
from __future__ import annotations

import pytest

from backend.planner.planning_errors import PlannerErrorCode, PlanningError
from backend.planner.tokenizer import MAX_COMMAND_CHARS, Token, TokenType, Tokenizer


@pytest.fixture
def tokenizer() -> Tokenizer:
    return Tokenizer()


# ── Happy-path tokenization ───────────────────────────────────────────────────

class TestBasicTokenization:
    def test_single_verb_target(self, tokenizer):
        tokens = tokenizer.tokenize("Open Chrome")
        assert [t.value for t in tokens] == ["open", "chrome"]
        assert all(t.type == TokenType.WORD for t in tokens)

    def test_lowercase_conversion(self, tokenizer):
        tokens = tokenizer.tokenize("OPEN CHROME")
        assert tokens[0].value == "open"
        assert tokens[1].value == "chrome"

    def test_leading_trailing_whitespace_stripped(self, tokenizer):
        tokens = tokenizer.tokenize("  open chrome  ")
        assert len(tokens) == 2

    def test_extra_internal_whitespace_collapsed(self, tokenizer):
        tokens = tokenizer.tokenize("open    chrome")
        assert len(tokens) == 2


class TestConnectorTokenization:
    def test_and_is_connector(self, tokenizer):
        tokens = tokenizer.tokenize("open chrome and github")
        connector = tokens[2]
        assert connector.type == TokenType.CONNECTOR
        assert connector.value == "and"

    def test_then_is_sequence(self, tokenizer):
        tokens = tokenizer.tokenize("open chrome then github")
        assert tokens[2].type == TokenType.SEQUENCE
        assert tokens[2].value == "then"

    def test_ampersand_is_connector(self, tokenizer):
        tokens = tokenizer.tokenize("open chrome & github")
        assert tokens[2].type == TokenType.CONNECTOR
        assert tokens[2].value == "&"

    def test_comma_is_connector(self, tokenizer):
        tokens = tokenizer.tokenize("open chrome, github")
        # After splitting: ["open", "chrome", ",", "github"]
        connector = next(t for t in tokens if t.value == ",")
        assert connector.type == TokenType.CONNECTOR

    def test_multi_connector_command(self, tokenizer):
        tokens = tokenizer.tokenize("open chrome and github then downloads")
        values = [t.value for t in tokens]
        assert values == ["open", "chrome", "and", "github", "then", "downloads"]


class TestMultiWordInput:
    def test_vs_code_tokenized_as_two_words(self, tokenizer):
        tokens = tokenizer.tokenize("open vs code")
        assert [t.value for t in tokens] == ["open", "vs", "code"]
        assert all(t.type == TokenType.WORD for t in tokens)

    def test_google_chrome(self, tokenizer):
        tokens = tokenizer.tokenize("open google chrome")
        assert [t.value for t in tokens] == ["open", "google", "chrome"]


class TestUnicodeHandling:
    def test_unicode_space_collapsed(self, tokenizer):
        tokens = tokenizer.tokenize("open\u00a0chrome")   # non-breaking space
        assert len(tokens) == 2

    def test_full_width_letters_normalized(self, tokenizer):
        # NFKC normalisation converts fullwidth ASCII letters
        tokens = tokenizer.tokenize("\uff4f\uff50\uff45\uff4e chrome")  # ｏｐｅｎ
        assert tokens[0].value == "open"


# ── Error handling ────────────────────────────────────────────────────────────

class TestEmptyInput:
    def test_empty_string(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("")
        assert exc.value.error_code == PlannerErrorCode.EMPTY_COMMAND

    def test_whitespace_only(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("   ")
        assert exc.value.error_code == PlannerErrorCode.EMPTY_COMMAND


class TestLengthLimit:
    def test_exactly_at_limit_is_allowed(self, tokenizer):
        # Build a valid command that is <= MAX_COMMAND_CHARS.
        # "open chrome" repeated with connectors stays well under 500 chars
        # and must tokenize without a COMMAND_TOO_LONG error.
        cmd = ("open chrome and " * 10).rstrip()   # ~160 chars — valid
        tokens = tokenizer.tokenize(cmd)
        assert len(tokens) > 0

    def test_one_over_limit_raises(self, tokenizer):
        cmd = "a" * (MAX_COMMAND_CHARS + 1)
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize(cmd)
        assert exc.value.error_code == PlannerErrorCode.COMMAND_TOO_LONG


class TestShellMetacharacters:
    def test_double_ampersand_rejected(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("open chrome && del C:\\")
        assert exc.value.error_code == PlannerErrorCode.TOKENIZATION_ERROR

    def test_pipe_rejected(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("open chrome | rm -rf /")
        assert exc.value.error_code == PlannerErrorCode.TOKENIZATION_ERROR

    def test_semicolon_rejected(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("open chrome; open vscode")
        assert exc.value.error_code == PlannerErrorCode.TOKENIZATION_ERROR

    def test_backtick_rejected(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("open `chrome`")
        assert exc.value.error_code == PlannerErrorCode.TOKENIZATION_ERROR

    def test_dollar_rejected(self, tokenizer):
        with pytest.raises(PlanningError) as exc:
            tokenizer.tokenize("open $HOME")
        assert exc.value.error_code == PlannerErrorCode.TOKENIZATION_ERROR

    def test_single_ampersand_is_allowed(self, tokenizer):
        """Single & is a connector, not a shell metacharacter."""
        tokens = tokenizer.tokenize("open chrome & github")
        assert any(t.value == "&" for t in tokens)


class TestUnknownTokens:
    def test_at_symbol_preserved_as_unknown(self, tokenizer):
        tokens = tokenizer.tokenize("open @chrome")
        # tokens: [WORD("open"), UNKNOWN("@chrome")]
        assert tokens[1].type == TokenType.UNKNOWN
        assert tokens[1].value == "@chrome"

    def test_hash_preserved_as_unknown(self, tokenizer):
        tokens = tokenizer.tokenize("open #chrome")
        assert tokens[1].type == TokenType.UNKNOWN
        assert tokens[1].value == "#chrome"


class TestCustomGrammarConfig:
    def test_custom_grammar_config_is_respected(self):
        from backend.config.config_loader import GrammarConfig
        config = GrammarConfig(
            version="1.0",
            connectors=("plus", "with"),
            sequences=("next", "followed-by")
        )
        custom_tokenizer = Tokenizer(grammar_config=config)
        tokens = custom_tokenizer.tokenize("open chrome plus github next close vscode")
        # Expected:
        # [WORD("open"), WORD("chrome"), CONNECTOR("plus"), WORD("github"), SEQUENCE("next"), WORD("close"), WORD("vscode")]
        assert tokens[2].type == TokenType.CONNECTOR
        assert tokens[2].value == "plus"
        assert tokens[4].type == TokenType.SEQUENCE
        assert tokens[4].value == "next"


class TestTokenDataclass:
    def test_token_repr(self):
        t = Token(type=TokenType.WORD, value="chrome")
        assert "WORD" in repr(t)
        assert "chrome" in repr(t)

    def test_token_is_frozen(self):
        t = Token(type=TokenType.WORD, value="chrome")
        with pytest.raises((AttributeError, TypeError)):
            t.value = "vscode"  # type: ignore[misc]

