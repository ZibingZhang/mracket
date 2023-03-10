"""The mutation runner result."""
from __future__ import annotations

import abc
import enum
from collections.abc import Iterator

from mracket import mutation
from mracket.runner import output, score


class RunnerResult(metaclass=abc.ABCMeta):
    """A runner result."""

    def __init__(self, filepath: str, execution_succeeded: bool) -> None:
        self.filepath = filepath
        self.execution_succeeded = execution_succeeded

    @property
    def score(self) -> score.MutationScore | None:
        return None

    def to_dict(self) -> dict:
        return {
            "filepath": self.filepath,
            "execution-succeeded": self.execution_succeeded,
        }


class RunnerFailure(RunnerResult, Exception):
    """A runner failure."""

    class Reason(enum.Enum):
        """Runner failure reason."""

        READER_ERROR = "Reader unable to read program"
        NOT_DRRACKETY = "Program missing DrRacket prefix"
        NOT_WELL_FORMED_PROGRAM = "Program not well-formed"
        NON_ZERO_MUTANT_RETURNCODE = "Non-zero returncode when running mutant"
        NON_ZERO_UNMODIFIED_RETURNCODE = "Non-zero returncode when running unmodified source"
        UNKNOWN_ERROR = "Unknown error"
        UNMODIFIED_TEST_FAILURE = "Test failure when running unmodified source"

    def __init__(self, reason: Reason, **kwargs) -> None:
        RunnerResult.__init__(self, filepath="", execution_succeeded=False)
        Exception.__init__(self, reason.value)
        self.reason = reason
        self.dict = kwargs

    def to_dict(self) -> dict:
        return {
            **RunnerResult.to_dict(self),
            "reason": self.reason.value,
            **self.dict,
        }


class RunnerSuccess(RunnerResult):
    """A runner success."""

    def __init__(self, filepath: str) -> None:
        super().__init__(filepath=filepath, execution_succeeded=True)
        self.mutations: list[mutation.Mutation] = []
        self.unmodified_result: output.ProgramOutput | None = None
        self.mutant_results: Iterator[output.MutantOutput] | None = None

        self._evaluated_mutant_results: list[output.MutantOutput] = []
        self._total = 0
        self._killed = 0
        self._execution_error = 0

    @property
    def score(self) -> score.MutationScore:
        self._evaluate_mutants()
        return score.MutationScore(total=self._total, killed=self._killed, execution_error=self._execution_error)

    def to_dict(self) -> dict:
        self._evaluate_mutants()
        mutation_results: list[dict[str, bool | str]] = []
        for evaluated_mutant_result in self._evaluated_mutant_results:
            mutation_result: dict[str, bool | str] = {"explanation": evaluated_mutant_result.mutation.explanation}
            if evaluated_mutant_result.stderr != "":
                mutation_result["execution-error"] = evaluated_mutant_result.stderr
            else:
                mutation_result["killed"] = evaluated_mutant_result.failed > 0
            mutation_results.append(mutation_result)

        dct: dict = {
            **super().to_dict(),
            "summary": {"total": self._total, "killed": self._killed},
            "mutations": mutation_results,
        }
        if self._execution_error > 0:
            dct["summary"]["execution-error"] = self._execution_error
        return dct

    def _evaluate_mutants(self) -> None:
        if self.mutant_results is None:
            return None

        killed = 0
        execution_error = 0
        i = -1
        for i, result in enumerate(self.mutant_results):
            self._evaluated_mutant_results.append(result)
            if result.stderr:
                execution_error += 1
            elif result.failed > 0:
                killed += 1

        self._total = i + 1
        self._killed = killed
        self._execution_error = execution_error
        self.mutant_results = None
