"""Tests for mracket.mutation.mutator."""
from __future__ import annotations

from mracket.mutation.generator import ProcedureReplacement
from mracket.mutation.mutator import Mutator
from mracket.reader.lexer import Lexer
from mracket.reader.parser import Parser


def test_name_specific_mutator() -> None:
    mutator_for_f = Mutator([ProcedureReplacement({"+": ["-"]})])
    mutator = Mutator([ProcedureReplacement({"+": ["*"]})], {"f": mutator_for_f})

    source = "#lang racket\n(+ 1)\n(define (f) (+ 1))"
    program = Parser().parse(Lexer().tokenize(source))

    mutations = list(mutator.visit(program))

    assert len(mutations) == 2

    mutation_1, mutation_2 = mutations

    assert mutation_1.original.token.source == "+"
    assert mutation_1.original.token.offset == 14
    assert mutation_1.replacement.token.source == "*"

    assert mutation_2.original.token.source == "+"
    assert mutation_2.original.token.offset == 32
    assert mutation_2.replacement.token.source == "-"
