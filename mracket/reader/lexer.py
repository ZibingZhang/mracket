"""A lexer for Racket programs."""
# The lexer is based off of Racket's reader: https://docs.racket-lang.org/reference/reader.html
from __future__ import annotations

import dataclasses
import enum
import re
from collections.abc import Generator, Sequence
from typing import cast

from mracket.reader import errors

# regex for numbers

# fmt: off
EXACTNESS = r"#[ei]"
SIGN = r"[+-]"

DIGIT_2 = r"[01]"
DIGIT_8 = fr"({DIGIT_2}|[234567])"
DIGIT_10 = fr"({DIGIT_8}|[89])"
DIGIT_16 = fr"({DIGIT_10}|[abcdef])"

DIGITS_POUND_2 = fr"{DIGIT_2}+#*"
DIGITS_POUND_8 = fr"{DIGIT_8}+#*"
DIGITS_POUND_10 = fr"{DIGIT_10}+#*"
DIGITS_POUND_16 = fr"{DIGIT_16}+#*"

UNSIGNED_INTEGER_2 = fr"{DIGIT_2}+"
UNSIGNED_INTEGER_8 = fr"{DIGIT_8}+"
UNSIGNED_INTEGER_10 = fr"{DIGIT_10}+"
UNSIGNED_INTEGER_16 = fr"{DIGIT_16}+"

EXACT_INTEGER_2 = fr"{SIGN}?{UNSIGNED_INTEGER_2}"
EXACT_INTEGER_8 = fr"{SIGN}?{UNSIGNED_INTEGER_8}"
EXACT_INTEGER_10 = fr"{SIGN}?{UNSIGNED_INTEGER_10}"
EXACT_INTEGER_16 = fr"{SIGN}?{UNSIGNED_INTEGER_16}"

UNSIGNED_RATIONAL_2 = fr"{UNSIGNED_INTEGER_2}(/{UNSIGNED_INTEGER_2})?"
UNSIGNED_RATIONAL_8 = fr"{UNSIGNED_INTEGER_8}(/{UNSIGNED_INTEGER_8})?"
UNSIGNED_RATIONAL_10 = fr"{UNSIGNED_INTEGER_10}(/{UNSIGNED_INTEGER_10})?"
UNSIGNED_RATIONAL_16 = fr"{UNSIGNED_INTEGER_16}(/{UNSIGNED_INTEGER_16})?"

EXACT_RATIONAL_2 = fr"{SIGN}?{UNSIGNED_RATIONAL_2}"
EXACT_RATIONAL_8 = fr"{SIGN}?{UNSIGNED_RATIONAL_8}"
EXACT_RATIONAL_10 = fr"{SIGN}?{UNSIGNED_RATIONAL_10}"
EXACT_RATIONAL_16 = fr"{SIGN}?{UNSIGNED_RATIONAL_16}"

EXACT_COMPLEX_2 = fr"{EXACT_RATIONAL_2}{SIGN}{UNSIGNED_RATIONAL_2}i"
EXACT_COMPLEX_8 = fr"{EXACT_RATIONAL_8}{SIGN}{UNSIGNED_RATIONAL_8}i"
EXACT_COMPLEX_10 = fr"{EXACT_RATIONAL_10}{SIGN}{UNSIGNED_RATIONAL_10}i"
EXACT_COMPLEX_16 = fr"{EXACT_RATIONAL_16}{SIGN}{UNSIGNED_RATIONAL_16}i"

EXACT_2 = fr"({EXACT_RATIONAL_2}|{EXACT_COMPLEX_2})"
EXACT_8 = fr"({EXACT_RATIONAL_8}|{EXACT_COMPLEX_8})"
EXACT_10 = fr"({EXACT_RATIONAL_10}|{EXACT_COMPLEX_10})"
EXACT_16 = fr"({EXACT_RATIONAL_16}|{EXACT_COMPLEX_16})"

INEXACT_SPECIAL = r"(inf\.0|nan\.0|inf\.f|nan\.f)"

EXP_MARK_16 = r"[sl]"
EXP_MARK_10 = fr"({EXP_MARK_16}|[def])"
EXP_MARK_8 = EXP_MARK_10
EXP_MARK_2 = EXP_MARK_10

INEXACT_SIMPLE_2 = fr"({UNSIGNED_INTEGER_2}?\.{DIGITS_POUND_2}|{DIGITS_POUND_2}/{DIGITS_POUND_2}|{DIGITS_POUND_2}\.?#*)"
INEXACT_SIMPLE_8 = fr"({UNSIGNED_INTEGER_8}?\.{DIGITS_POUND_8}|{DIGITS_POUND_8}/{DIGITS_POUND_8}|{DIGITS_POUND_8}\.?#*)"
INEXACT_SIMPLE_10 = fr"({UNSIGNED_INTEGER_10}?\.{DIGITS_POUND_10}|{DIGITS_POUND_10}/{DIGITS_POUND_10}|{DIGITS_POUND_10}\.?#*)"
INEXACT_SIMPLE_16 = fr"({UNSIGNED_INTEGER_16}?\.{DIGITS_POUND_16}|{DIGITS_POUND_16}/{DIGITS_POUND_16}|{DIGITS_POUND_16}\.?#*)"

INEXACT_NORMAL_2 = fr"{INEXACT_SIMPLE_2}({EXP_MARK_2}{EXACT_INTEGER_2})?"
INEXACT_NORMAL_8 = fr"{INEXACT_SIMPLE_8}({EXP_MARK_8}{EXACT_INTEGER_8})?"
INEXACT_NORMAL_10 = fr"{INEXACT_SIMPLE_10}({EXP_MARK_10}{EXACT_INTEGER_10})?"
INEXACT_NORMAL_16 = fr"{INEXACT_SIMPLE_16}({EXP_MARK_16}{EXACT_INTEGER_16})?"

INEXACT_UNSIGNED_2 = fr"({INEXACT_NORMAL_2}|{INEXACT_SPECIAL})"
INEXACT_UNSIGNED_8 = fr"({INEXACT_NORMAL_8}|{INEXACT_SPECIAL})"
INEXACT_UNSIGNED_10 = fr"({INEXACT_NORMAL_10}|{INEXACT_SPECIAL})"
INEXACT_UNSIGNED_16 = fr"({INEXACT_NORMAL_16}|{INEXACT_SPECIAL})"

INEXACT_REAL_2 = fr"({SIGN}?{INEXACT_NORMAL_2}|{SIGN}{INEXACT_SPECIAL})"
INEXACT_REAL_8 = fr"({SIGN}?{INEXACT_NORMAL_8}|{SIGN}{INEXACT_SPECIAL})"
INEXACT_REAL_10 = fr"({SIGN}?{INEXACT_NORMAL_10}|{SIGN}{INEXACT_SPECIAL})"
INEXACT_REAL_16 = fr"({SIGN}?{INEXACT_NORMAL_16}|{SIGN}{INEXACT_SPECIAL})"

INEXACT_COMPLEX_2 = fr"({INEXACT_REAL_2}?{SIGN}{INEXACT_UNSIGNED_2}i|{INEXACT_REAL_2}@{INEXACT_REAL_2})"
INEXACT_COMPLEX_8 = fr"({INEXACT_REAL_8}?{SIGN}{INEXACT_UNSIGNED_8}i|{INEXACT_REAL_8}@{INEXACT_REAL_8})"
INEXACT_COMPLEX_10 = fr"({INEXACT_REAL_10}?{SIGN}{INEXACT_UNSIGNED_10}i|{INEXACT_REAL_10}@{INEXACT_REAL_10})"
INEXACT_COMPLEX_16 = fr"({INEXACT_REAL_16}?{SIGN}{INEXACT_UNSIGNED_16}i|{INEXACT_REAL_16}@{INEXACT_REAL_16})"

INEXACT_2 = fr"({INEXACT_REAL_2}|{INEXACT_COMPLEX_2})"
INEXACT_8 = fr"({INEXACT_REAL_8}|{INEXACT_COMPLEX_8})"
INEXACT_10 = fr"({INEXACT_REAL_10}|{INEXACT_COMPLEX_10})"
INEXACT_16 = fr"({INEXACT_REAL_16}|{INEXACT_COMPLEX_16})"

NUMBER_2 = fr"({EXACT_2}|{INEXACT_2})"
NUMBER_8 = fr"({EXACT_8}|{INEXACT_8})"
NUMBER_10 = fr"({EXACT_10}|{INEXACT_10})"
NUMBER_16 = fr"({EXACT_16}|{INEXACT_16})"

GENERAL_NUMBER_2 = fr"({EXACTNESS})?{NUMBER_2}"
GENERAL_NUMBER_8 = fr"({EXACTNESS})?{NUMBER_8}"
GENERAL_NUMBER_10 = fr"({EXACTNESS})?{NUMBER_10}"
GENERAL_NUMBER_16 = fr"({EXACTNESS})?{NUMBER_16}"

GENERAL_NUMBER = fr"(#b{GENERAL_NUMBER_2}|#o{GENERAL_NUMBER_8}|(#d)?{GENERAL_NUMBER_10}|#x{GENERAL_NUMBER_16})"
LEADING_EXACTNESS_NUMBER = fr"{EXACTNESS}(#b{NUMBER_2}|#o{NUMBER_8}|(#d)?{NUMBER_10}|#x{NUMBER_16})"

# regex for strings

STRING_CHARACTER = fr"""([^\\\"]|\\([abtnvfre\"']|{DIGIT_8}{{1,3}}|x{DIGIT_16}{{1,2}}|u{DIGIT_16}{{1,4}}(\\u{DIGIT_16}{{1,4}})?|U{DIGIT_16}{{1,8}})|\\\
)"""

# regex for symbols

LEADING_SYMBOL_CHARACTER = r"[^()[\]{}\",'`;#|\\\s]"
SYMBOL_CHARACTER = r"[^()[\]{}\",'`;|\\\s]"
EXTENDED_SYMBOL_CHARACTER = fr"({SYMBOL_CHARACTER}|\s)"
ESCAPED_SYMBOL_CHARACTERS = fr"(\\{EXTENDED_SYMBOL_CHARACTER}|\|{EXTENDED_SYMBOL_CHARACTER}*\|)"

# regex for tokens

ABBREVIATED_BOOLEAN = re.compile(r"#[TtFf]")
BOOLEAN = re.compile(r"#(true|false)")
CHARACTER = re.compile(fr"#\\(null?|backspace|tab|newline|linefeed|vtab|page|return|space|rubout|{DIGIT_8}{{3}}|u{DIGIT_16}{{1,4}}|U{DIGIT_16}{{1,8}}|[a-zA-Z](?![a-zA-Z])|[0-7](?![0-7])|[^a-zA-Z0-7])")
DELIMITER = re.compile(r"(,@|[()[\]{}'`,])")
LINE_COMMENT = re.compile(r";.*")
NUMBER = re.compile(fr"({GENERAL_NUMBER}|{LEADING_EXACTNESS_NUMBER})(?=$|[()[\]{{}}'`,\"\s])", re.IGNORECASE)
READER_DIRECTIVE = re.compile(r"#(lang|reader).*")
STRING = re.compile(fr'"{STRING_CHARACTER}*"', re.DOTALL)
SYMBOL = re.compile(fr"({ESCAPED_SYMBOL_CHARACTERS}|{LEADING_SYMBOL_CHARACTER})({ESCAPED_SYMBOL_CHARACTERS}|{SYMBOL_CHARACTER})*", re.DOTALL)
WHITESPACE = re.compile(r"\s+")
# fmt: on


class TokenType(enum.Enum):
    """The type of token."""

    BOOLEAN = "BOOLEAN"
    CHARACTER = "CHARACTER"
    COMMENT = "COMMENT"
    DELIMITER = "DELIMITER"
    EOF = "EOF"
    LPAREN = "LPAREN"
    NUMBER = "NUMBER"
    QUASIQUOTE = "QUASIQUOTE"
    QUOTE = "QUOTE"
    READER_DIRECTIVE = "READER DIRECTIVE"
    RPAREN = "RPAREN"
    STRING = "STRING"
    SYMBOL = "SYMBOL"
    UNQUOTE = "UNQUOTE"
    UNQUOTE_SPLICING = "UNQUOTE SPLICING"
    WHITESPACE = "WHITESPACE"


TOKEN_PATTERNS: Sequence[tuple[re.Pattern, TokenType]] = (
    (BOOLEAN, TokenType.BOOLEAN),
    (ABBREVIATED_BOOLEAN, TokenType.BOOLEAN),
    (CHARACTER, TokenType.CHARACTER),
    (NUMBER, TokenType.NUMBER),
    (STRING, TokenType.STRING),
    (READER_DIRECTIVE, TokenType.READER_DIRECTIVE),
    (SYMBOL, TokenType.SYMBOL),
    (DELIMITER, TokenType.DELIMITER),
)


@dataclasses.dataclass(frozen=True)
class Token:
    """A lexical token."""

    type: TokenType
    offset: int
    lineno: int
    colno: int
    source: str = ""

    def __post_init__(self):
        assert self.type is not TokenType.DELIMITER
        if self.type is not TokenType.EOF:
            assert self.source != ""

    @staticmethod
    def from_source(token_type: TokenType, source: str) -> Token:
        """Create a non-positional Token.

        :param token_type: The type of token
        :param source: Racket source code of the token
        :return: A non-positional Token
        """
        return Token(type=token_type, offset=-1, lineno=-1, colno=-1, source=source)


EOF_TOKEN = Token(type=TokenType.EOF, offset=-1, lineno=-1, colno=-1)
DUMMY_TOKEN = cast(Token, None)
DUMMY_ELSE_SYMBOL_TOKEN = Token(type=TokenType.SYMBOL, offset=-1, lineno=-1, colno=-1, source="else")
DUMMY_LPAREN_TOKEN = Token(type=TokenType.LPAREN, offset=-1, lineno=-1, colno=-1, source="(")
DUMMY_RPAREN_TOKEN = Token(type=TokenType.RPAREN, offset=-1, lineno=-1, colno=-1, source="(")


class Lexer:
    """A lexer for Racket programs."""

    def __init__(self):
        self._truncated_source = ""
        self._offset = -1
        self._lineno = -1
        self._colno = -1

    def tokenize(self, source: str) -> Generator[Token, None, None]:
        """Convert the source program into tokens.

        :param source: Racket source code
        :return: Generator of tokens
        """
        self._truncated_source = source
        self._offset = 0
        self._lineno = 1
        self._colno = 1

        while (token := self._next_token()) is not None:
            yield token
        yield EOF_TOKEN

    def _next_token(self) -> Token | None:
        while True:
            # skip whitespace
            if re_match := re.match(WHITESPACE, self._truncated_source):
                self._make_token(TokenType.WHITESPACE, re_match.group())
                continue
            # skip line comment
            if re_match := re.match(LINE_COMMENT, self._truncated_source):
                self._make_token(TokenType.COMMENT, re_match.group())
                continue
            # TODO: handle multiline comments, need to keep track of recursion level
            break

        # return early if EOF
        if len(self._truncated_source) == 0:
            return None

        # try to match each pattern
        for pattern, token_type in TOKEN_PATTERNS:
            if re_match := re.match(pattern, self._truncated_source):
                return self._make_token(token_type, re_match.group())

        raise errors.UnrecognizedTokenError(self._offset)

    def _make_token(self, token_type: TokenType, token_source: str) -> Token:
        # punctuators have different types
        if token_type is TokenType.DELIMITER:
            if token_source in "([{":
                token_type = TokenType.LPAREN
            elif token_source in ")]}":
                token_type = TokenType.RPAREN
            elif token_source in "`":
                token_type = TokenType.QUASIQUOTE
            elif token_source in "'":
                token_type = TokenType.QUOTE
            elif token_source in ",":
                token_type = TokenType.UNQUOTE
            elif token_source in ",@":
                token_type = TokenType.UNQUOTE_SPLICING

        token = Token(type=token_type, offset=self._offset, lineno=self._lineno, colno=self._colno, source=token_source)
        self._advance_position(token_source)
        self._truncate_source(len(token.source))
        return token

    def _advance_position(self, token_source: str) -> None:
        self._offset += len(token_source)
        for character in token_source:
            if character == "\n":
                self._lineno += 1
                self._colno = 0
            else:
                self._colno += 1

    def _truncate_source(self, size: int) -> None:
        self._truncated_source = self._truncated_source[size:]
