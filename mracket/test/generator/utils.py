"""Utilities for testing mutation generators."""
from __future__ import annotations

from collections.abc import Generator

from mracket import mutation
from mracket.mutation import mutator
from mracket.mutation.generator import base
from mracket.reader import lexer, parser


def apply_generator(generator: base.BaseMutationGenerator, source: str) -> Generator[mutation.Mutation, None, None]:
    tree = parser.Parser(lexer.Lexer(f"#lang racket\n{source}").tokenize()).parse()
    mutator_ = mutator.Mutator(generators=[generator])
    return mutator_.visit(tree)
