"""Tests for mracket.mutation.generator.procedure_replacement."""
from __future__ import annotations

import pytest

from mracket import test
from mracket.mutation.generator.procedure_replacement import ProcedureReplacement


@pytest.mark.parametrize(
    "mapping,source,mutation_count",
    [
        [{"+": {"-"}}, "(- 1)", 0],
        [{"+": {"-"}}, "(+ 1)", 1],
        [{"+": {"-", "*", "/"}}, "(+ 1 (+ 2 3))", 6],
    ],
)
def test_procedure_replacement(mapping: dict[str, set[str]], source: str, mutation_count: int) -> None:
    generator = ProcedureReplacement(mapping)
    mutations = test.generator.utils.apply_generator(generator, source)
    assert len(list(mutations)) == mutation_count
