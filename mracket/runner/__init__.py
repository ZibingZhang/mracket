"""The mutation runner."""
from __future__ import annotations

import itertools
import os.path
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Generator, Iterator, Iterable

from mracket import mutation
from mracket.mutation import applier, generator, mutator
from mracket.reader import lexer, parser, syntax, stringify
from mracket.runner import result

DRRACKET_PREFIX = ";; The first three lines of this file were inserted by DrRacket."
PROGRAM_SUFFIX = "(require test-engine/racket-tests)\n(test)"


class Runner:
    BATCH_SIZE = 10
    DIR = tempfile.gettempdir()

    """The mutation testing runner."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.success = result.RunnerSuccess(filename)

    @staticmethod
    def check_preconditions() -> None:
        if shutil.which("racket") is None:
            raise FileNotFoundError("Cannot find the racket executable.")

    @staticmethod
    def check_file(filename: str) -> None:
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"{filename} not found.")
        process = subprocess.Popen(["racket", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if len(stderr) > 0:
            raise result.RunnerFailure(reason=result.Reason.NOT_WELL_FORMED_PROGRAM)

    def run(self) -> None:
        self.check_file(self.filename)
        program = self.build_syntax_tree()
        self.run_original(program)
        mutations = self.generate_mutations(program)
        mutation_mutants = self.apply_mutations(program, mutations)
        self.success.mutant_results = self.run_mutants(mutation_mutants)

    def build_syntax_tree(self) -> syntax.RacketProgramNode:
        with open(self.filename) as f:
            source = f.read()
        if not source.startswith(DRRACKET_PREFIX):
            raise result.RunnerFailure(reason=result.Reason.NOT_DRRACKETY)
        tokens = lexer.Lexer(source).tokenize()
        program = parser.Parser(tokens).parse()
        return program

    def run_original(self, program: syntax.RacketProgramNode) -> None:
        filename = Runner._create_file(Runner._rand_filename(), stringify.Stringifier().visit(program))
        process = self._run_program(filename)
        stdout, stderr = process.communicate()
        Runner._delete_file(filename)
        if process.returncode != 0:
            print(stdout, stderr)
            raise result.RunnerFailure(
                reason=result.Reason.NON_ZERO_ORIGINAL_RETURNCODE, returncode=process.returncode, stderr=stderr
            )
        self.success.base_result = result.ProgramResult(stdout)

    def generate_mutations(self, program: syntax.RacketProgramNode) -> Iterator[mutation.Mutation]:
        mutation_generator = mutator.Mutator([generator.ProcedureReplacement({"+": {"-", "*"}})])
        mutations = mutation_generator.visit(program)
        return mutations

    def apply_mutations(self, program: syntax.RacketProgramNode, mutations: Iterator[mutation.Mutation]) -> Iterator[tuple[mutation.Mutation, str]]:
        mutation_applier = applier.MutationApplier(program, list(mutations))
        mutation_mutants = mutation_applier.apply_mutations()
        return mutation_mutants

    def run_mutants(self, mutation_mutants: Iterator[tuple[mutation.Mutation, str]]) -> Generator[result.MutantResult, None, None]:
        for batch in self._batched(mutation_mutants):
            filenames = [str(uuid.uuid4()) for _ in range(Runner.BATCH_SIZE)]
            mutation_processes = []
            for (mut, mutant), filename in zip(batch, filenames):
                filename = Runner._create_file(filename, mutant)
                process = self._run_program(filename)
                mutation_processes.append((mut, process))
                Runner._delete_file(filename)

            for mut, process in mutation_processes:
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print(stdout, stderr)
                    raise result.RunnerFailure(
                        reason=result.Reason.NON_ZERO_MUTANT_RETURNCODE, returncode=process.returncode, stderr=stderr
                    )
                yield result.MutantResult(stdout, mut)

    @staticmethod
    def _batched(iterable: Iterable):
        it = iter(iterable)
        while batch := tuple(itertools.islice(it, Runner.BATCH_SIZE)):
            yield batch

    @staticmethod
    def _create_file(filename: str, source: str) -> str:
        filename = os.path.join(Runner.DIR, filename)
        with open(filename, "w") as f:
            f.write(source)
        return filename

    @staticmethod
    def _delete_file(filename: str) -> None:
        os.remove(os.path.join(Runner.DIR, filename))

    @staticmethod
    def _rand_filename() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def _run_program(filename: str) -> subprocess.Popen:
        process = subprocess.Popen(["racket", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
