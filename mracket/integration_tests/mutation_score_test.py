"""Integration tests for mutation score."""
from __future__ import annotations

import pytest

from mracket import test
from mracket.mutation.generator import (
    ProcedureApplicationReplacement,
    ProcedureReplacement,
)
from mracket.mutation.generator.base import BaseMutationGenerator
from mracket.mutation.mutator import Mutator
from mracket.runner import Runner


@pytest.mark.parametrize(
    "filename,mutation_generator,total,killed",
    [
        ["score-0.rkt", ProcedureReplacement({}), 0, 0],
        ["score-1.rkt", ProcedureReplacement({"+": ["-", "*"]}), 0, 0],
        ["score-2.rkt", ProcedureReplacement({"+": ["-", "*"]}), 2, 1],
        ["score-1.rkt", ProcedureApplicationReplacement({"+": ["1", "4"]}), 0, 0],
        ["score-2.rkt", ProcedureApplicationReplacement({"+": ["1", "4"]}), 2, 1],
    ],
)
@pytest.mark.slow
def test_single_generator(filename: str, mutation_generator: BaseMutationGenerator, total: int, killed: int) -> None:
    filepath = next(test.inputs.file_paths(filename))
    runner = Runner(Mutator([mutation_generator]), filepath)
    runner.run()
    score = runner.result.score
    assert score is not None
    assert score.total == total
    assert score.killed == killed
