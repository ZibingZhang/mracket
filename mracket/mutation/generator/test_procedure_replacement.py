"""Tests for mracket.mutation.generator.procedure_replacement."""
from __future__ import annotations

from mracket import test
from mracket.mutation.generator.procedure_replacement import ProcedureReplacement


def test_replace_plus() -> None:
    generator = ProcedureReplacement({"+": {"-", "*", "/"}})
    source = "(+ 1 (+ 2 3))"
    mutations = test.generator.utils.apply_generator(generator, source)
    assert len(list(mutations)) == 6
