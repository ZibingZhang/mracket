"""Utilities for testing mutation generators."""
from __future__ import annotations

from collections.abc import Generator

from mracket import mutation
from mracket.mutation import mutator
from mracket.mutation.generator import base
from mracket.reader import lexer, parser


def apply_generator(generator: base.BaseMutationGenerator, source: str) -> Generator[mutation.Mutation, None, None]:
    """Apply the mutation generator to the source code.

    :param generator: A muation generator
    :param source: Racket source code
    :return: Generator of mutations
    """
    program = parser.Parser().parse(lexer.Lexer().tokenize(f"#lang racket\n{source}"))
    mutator_ = mutator.Mutator(generators=[generator])
    return mutator_.visit(program)
