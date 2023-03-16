"""Utilities for testing mutation generators."""
from __future__ import annotations

from collections.abc import Generator

from mracket import mutation
from mracket.mutation import applier, mutator
from mracket.mutation.generator import base
from mracket.reader import lexer, parser


def apply_generator(generator: base.BaseMutationGenerator, source: str) -> Generator[mutation.Mutation, None, None]:
    """Apply the mutation generator to the source code.

    :param generator: Muation generator
    :param source: Racket source code
    :return: Generator of mutations
    """
    program = parser.Parser().parse(lexer.Lexer().tokenize(f"#lang racket\n{source}"))
    mutator_ = mutator.Mutator(generators=[generator])
    return mutator_.generate_mutations(program)


def assert_mutants(generator: base.BaseMutationGenerator, source: str, mutants: list[str]) -> None:
    """Assert the generator produces the mutants from the source.

    :param generator: Mutation generator
    :param source: Racket source code
    :param mutants: Expected mutants
    """
    program = parser.Parser().parse(lexer.Lexer().tokenize(f"#lang racket\n{source}"))
    mutator_ = mutator.Mutator(generators=[generator])
    for actual_mutant, expected_mutant in zip(
        applier.MutationApplier(program, list(mutator_.generate_mutations(program))).visit(program), mutants
    ):
        assert actual_mutant.source == f"#lang racket\n{expected_mutant}"
