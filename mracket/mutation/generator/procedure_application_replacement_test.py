"""Tests for mracket.mutation.generator.procedure_replacement."""
from __future__ import annotations

from collections.abc import Mapping

import pytest

from mracket import test
from mracket.mutation.generator.procedure_application_replacement import (
    ProcedureApplicationReplacement,
)


@pytest.mark.parametrize(
    "mappings,source,mutation_count",
    [
        [{"and": ["#t", "#f"]}, "(or #t)", 0],
        [{"and": ["#t", "#f"]}, "(and #t)", 2],
        [{"and": ["#t", "#f"], "or": ["#t", "#f"]}, "(and (or #t))", 4],
    ],
)
def test_mutation_count(mappings: Mapping[str, list[str]], source: str, mutation_count: int) -> None:
    generator = ProcedureApplicationReplacement(mappings)
    mutations = test.generator.utils.apply_generator(generator, source)
    assert len(list(mutations)) == mutation_count


@pytest.mark.parametrize(
    "mappings,source,mutants",
    [
        [{"and": ["#t", "#f"]}, "(and #t)", ["#t", "#f"]],
        [{"and": ["#t", "#f"], "or": ["#t", "#f"]}, "(and (or #t))", ["#t", "#f", "(and #t)", "(and #f)"]],
        [{"list": ["'()"]}, "(list 1 2 3)", ["(quote ())"]],
    ],
)
def test_mutants(mappings: Mapping[str, list[str]], source: str, mutants: list[str]) -> None:
    test.generator.utils.assert_mutants(ProcedureApplicationReplacement(mappings), source, mutants)
