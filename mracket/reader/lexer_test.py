"""Tests for mracket.reader.lexer."""
from __future__ import annotations

import pytest

from mracket.reader.errors import LexerError
from mracket.reader.lexer import Lexer, TokenType


@pytest.mark.parametrize(
    "token_type,source,strings",
    [
        [None, "", ""],
        [TokenType.LPAREN, "([{", ["(", "[", "{"]],
        [TokenType.RPAREN, ")]}", [")", "]", "}"]],
        [TokenType.QUASIQUOTE, "`", ["`"]],
        [TokenType.QUOTE, "'", ["'"]],
        [TokenType.UNQUOTE, ",", [","]],
        [TokenType.BOOLEAN, "#t #T #true #f #F #false", ["#t", "#T", "#true", "#f", "#F", "#false"]],
        [TokenType.CHARACTER, r"#\a #\1 #\λ", [r"#\a", r"#\1", r"#\λ"]],
        [TokenType.CHARACTER, r"#\123 #\uabcd #\Uabcdef01", [r"#\123", r"#\uabcd", r"#\Uabcdef01"]],
        [TokenType.NUMBER, "123 +123 -123", ["123", "+123", "-123"]],
        [TokenType.NUMBER, "1/2 +1/2 -1/2", ["1/2", "+1/2", "-1/2"]],
        [TokenType.NUMBER, "1# 1#. 1#.# 1#/1#", ["1#", "1#.", "1#.#", "1#/1#"]],
        [TokenType.NUMBER, "+inf.0 -nan.0 #e+inf.f #i-nan.f", ["+inf.0", "-nan.0", "#e+inf.f", "#i-nan.f"]],
        [TokenType.NUMBER, "#b101 #e#o7#. #x#eabc/de0", ["#b101", "#e#o7#.", "#x#eabc/de0"]],
        [TokenType.STRING, '"abc123"', ['"abc123"']],
        [TokenType.STRING, r'"\t\n" "\123" "\U0f"', [r'"\t\n"', r'"\123"', r'"\U0f"']],
        [
            TokenType.STRING,
            r'''"\
"''',
            [
                r'''"\
"'''
            ],
        ],
        [TokenType.SYMBOL, "abc || x| |y\\\nz", ["abc", "||", "x| |y\\\nz"]],
        [TokenType.SYMBOL, "1.. 1- 1a . ..", ["1..", "1-", "1a", ".", ".."]],
        [TokenType.SYMBOL, r"1#\1", [r"1#\1"]],
    ],
)
def test_tokenize_by_type(token_type: TokenType, source: str, strings: list[str]) -> None:
    tokens = Lexer(source).tokenize()
    assert len(tokens) == len(strings) + 1
    for token, string in zip(tokens, strings):
        assert token.source == string
        assert token.type == token_type


@pytest.mark.parametrize(
    "special_character",
    [
        "nul",
        "null",
        "backspace",
        "tab",
        "newline",
        "linefeed",
        "vtab",
        "page",
        "return",
        "space",
        "rubout",
    ],
)
def test_tokenize_special_characater(special_character: str) -> None:
    tokens = Lexer(rf"#\{special_character}").tokenize()
    assert len(tokens) - 1 == 1
    assert tokens[0].source == rf"#\{special_character}"


@pytest.mark.parametrize("source,strings", [[r"#\49", [r"#\4", "9"]], [r'1"a"', ["1", '"a"']]])
def test_tokenize_adjacent_tokens(source, strings: list[str]) -> None:
    tokens = Lexer(source).tokenize()
    assert len(tokens) == len(strings) + 1
    for token, source in zip(tokens, strings):
        assert token.source == source


@pytest.mark.parametrize("source", [r"#\ab", r"#\12"])
def test_tokenize_invalid_token(source) -> None:
    with pytest.raises(LexerError):
        Lexer(source).tokenize()
