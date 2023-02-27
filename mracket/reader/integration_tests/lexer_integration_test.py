"""Integration tests for mracket.reader.lexer."""
from __future__ import annotations

from mracket import test
from mracket.reader.lexer import Lexer


def test_token_position() -> None:
    for source in test.inputs.read_contents():
        tokens = Lexer().tokenize(source)

        for token in tokens:
            assert token.source == source[token.offset : token.offset + len(token.source)]
