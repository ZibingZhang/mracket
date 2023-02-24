"""Integration tests for mracket.reader.lexer."""
from __future__ import annotations

from mracket.reader.lexer import Lexer
from mracket.test_fixtures import inputs


def test_token_position() -> None:
    for source in inputs.read():
        lines = source.split("\n")
        tokens = Lexer(source).tokenize()

        for token in tokens:
            assert token.source == lines[token.lineno][token.colno : token.colno + len(token.source)]
