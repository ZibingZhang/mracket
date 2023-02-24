"""Integration tests for mracket.reader."""
from __future__ import annotations

from mracket.reader.lexer import Lexer
from mracket.reader.parser import Parser
from mracket.test_fixtures import inputs


def test_parse_program_succeeds() -> None:
    # tokenize and parse each file
    for source in inputs.read():
        tokens = Lexer(source).tokenize()
        Parser(tokens).parse()
