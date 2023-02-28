"""Tests for mracket.reader.parser."""
from __future__ import annotations

import pytest

from mracket.reader import lexer, parser, syntax


@pytest.mark.parametrize(
    "typ, source",
    [
        [syntax.RacketNameDefinitionNode, "(define x 1)"],
        [syntax.RacketNameDefinitionNode, "(define (x) 1)"],
        [syntax.RacketStructureDefinitionNode, "(define-struct posn [x y])"],
        [syntax.RacketLiteralNode, "#t"],
        [syntax.RacketLiteralNode, r"#\a"],
        [syntax.RacketLiteralNode, r"1"],
        [syntax.RacketLiteralNode, '"Hello, World!"'],
        [syntax.RacketNameNode, "identity"],
        [syntax.RacketCondNode, "(cond [#t 1])"],
        [syntax.RacketCondNode, "(if #t 1 2)"],
        [syntax.RacketLambdaNode, "(lambda (x) 1)"],
        [syntax.RacketLetNode, "(let ((x 1)) x)"],
        [syntax.RacketLocalNode, "(local ((define x 1)) x)"],
        [syntax.RacketLibraryRequireNode, "(require 2htdp/universe)"],
    ],
)
def test_parse_node_type(typ: type, source: str) -> None:
    tokens = lexer.Lexer().tokenize(f"#lang racket\n{source}")
    tree = parser.Parser().parse(tokens)
    assert isinstance(tree.statements[0], typ)
