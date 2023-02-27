"""Reader errors."""
from __future__ import annotations

import abc

from mracket.reader import lexer


class ReaderError(SyntaxError, metaclass=abc.ABCMeta):
    """A reader error."""


class IllegalStateError(ReaderError):
    """Reader is in an illegal state."""


class LexerError(ReaderError, metaclass=abc.ABCMeta):
    """A lexer error."""

    def __init__(self, offset: int, message: str = "") -> None:
        super().__init__(message)
        self.offset = offset


class UnexpectedEOFInStringError(LexerError):
    """Unexpected end-of-file while reading a string."""


class UnrecognizedTokenError(LexerError):
    """Unrecognized token."""


class ParserError(ReaderError, metaclass=abc.ABCMeta):
    """A parser error."""

    def __init__(self, current_token: lexer.Token, message: str = "") -> None:
        super().__init__(message)
        self.current_token = current_token


class ExpectedReaderDirective(ParserError):
    """Expected reader directive."""


class MismatchedParenthesesError(ParserError):
    """Mismatched parentheses."""

    def __init__(self, lparen: lexer.Token, rparen) -> None:
        super().__init__(rparen)
        self.lparen_token = lparen
        self.rparen_token = rparen


class UnexpectedEOFTokenError(ParserError):
    """Unexpected end-of-file token."""


class UnexpectedRightParenthesisError(ParserError):
    """Unexpected right parenthesis."""
