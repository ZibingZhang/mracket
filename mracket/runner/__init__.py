"""The mutation testing runner."""
from __future__ import annotations

import itertools
import os.path
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Generator, Iterable

from mracket import mutation
from mracket.mutation import applier, mutator
from mracket.reader import lexer, parser, stringify, syntax
from mracket.runner import result

DRRACKET_PREFIX = ";; The first three lines of this file were inserted by DrRacket."
PROGRAM_SUFFIX = "(require test-engine/racket-tests)\n(test)"


class Runner:
    """Runs a set of mutations on a file."""

    BATCH_SIZE = 10
    DIR = tempfile.gettempdir()

    def __init__(self, filename: str, mutator_: mutator.Mutator) -> None:
        self.filename = filename
        self.mutator = mutator_
        self.success = result.RunnerSuccess(filename)

    @staticmethod
    def check_preconditions() -> None:
        """Check that the necessary preconditions have been met."""
        if shutil.which("racket") is None:
            raise FileNotFoundError("Cannot find the racket executable.")

    @staticmethod
    def check_file_exists(filename: str) -> None:
        """Check that the file exists."""
        if not os.path.isfile(filename):
            raise FileNotFoundError(f"{filename} not found.")

    def run(self) -> None:
        """Evaluate the program and its mutants."""
        self.check_file_exists(self.filename)
        program = self.build_syntax_tree(self.filename)
        self.success.original_result = self.run_original(program)
        self.success.mutations = self.generate_mutations(self.mutator, program)
        mutation_mutants = self.apply_mutations(program, self.success.mutations)
        self.success.mutant_results = self.run_mutants(mutation_mutants)

    @staticmethod
    def build_syntax_tree(filename) -> syntax.RacketProgramNode:
        """Build an AST of the Racket program.

        :param filename: A Racket program filename
        :return: A program AST
        """
        with open(filename) as f:
            source = f.read()
        if not source.startswith(DRRACKET_PREFIX):
            raise result.RunnerFailure(reason=result.Reason.NOT_DRRACKETY)
        tokens = lexer.Lexer(source).tokenize()
        program = parser.Parser(tokens).parse()
        return program

    @staticmethod
    def run_original(program: syntax.RacketProgramNode) -> Generator[result.ProgramExecutionResult, None, None]:
        """Run the original program.

        The source code is not being run but rather the stringified program AST. The
        reason is that we want the positions of the errors, if any exist, to be the same
        between the original and the mutants.

        :param program: A Racket program AST
        :return: Result of running the original program
        """
        filename = Runner._random_filename()
        Runner._create_file(filename, stringify.Stringifier().visit(program))
        process = Runner._run_program(filename)
        stdout, stderr = process.communicate()
        Runner._delete_file(filename)
        if process.returncode != 0 or len(stderr) > 0:
            raise result.RunnerFailure(
                reason=result.Reason.NON_ZERO_ORIGINAL_RETURNCODE, returncode=process.returncode, stderr=stderr
            )
        yield result.ProgramExecutionResult(stdout)

    @staticmethod
    def generate_mutations(mutator_: mutator.Mutator, program: syntax.RacketProgramNode) -> list[mutation.Mutation]:
        """Generate mutations.

        :param mutator_: A mutator
        :param program: A program to be mutated
        :return: List of mutations
        """
        mutations = mutator_.visit(program)
        return list(mutations)

    @staticmethod
    def apply_mutations(
        program: syntax.RacketProgramNode, mutations: Iterable[mutation.Mutation]
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        """Apply the mutations.

        :param program: A program to mutate
        :param mutations: Iterator of mutations to apply to the program
        :return: A generator of mutation-mutant pairs
        """
        mutation_applier = applier.MutationApplier(program, list(mutations))
        mutation_mutants = mutation_applier.apply_mutations()
        return mutation_mutants

    @staticmethod
    def run_mutants(
        mutation_mutants: Iterable[tuple[mutation.Mutation, str]]
    ) -> Generator[result.MutantExecutionResult, None, None]:
        """Run the mutants.

        :param mutation_mutants: An iterator of mutation-mutant pairs
        :return: A generator of mutant execution results
        """
        for batch in Runner._batched(mutation_mutants):
            filenames = [Runner._random_filename() for _ in range(Runner.BATCH_SIZE)]
            mutation_processes = []
            for (mut, mutant), filename in zip(batch, filenames):
                Runner._create_file(filename, mutant)
                process = Runner._run_program(filename)
                mutation_processes.append((mut, process))

            for (mut, process), filename in zip(mutation_processes, filenames):
                stdout, stderr = process.communicate()
                Runner._delete_file(filename)
                if process.returncode != 0 or len(stderr) > 0:
                    raise result.RunnerFailure(
                        reason=result.Reason.NON_ZERO_MUTANT_RETURNCODE, returncode=process.returncode, stderr=stderr
                    )
                yield result.MutantExecutionResult(stdout, mut)

    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    @staticmethod
    def _batched(iterable: Iterable):
        it = iter(iterable)
        while batch := tuple(itertools.islice(it, Runner.BATCH_SIZE)):
            yield batch

    @staticmethod
    def _random_filename() -> str:
        return os.path.join(Runner.DIR, str(uuid.uuid4()))

    @staticmethod
    def _create_file(filename: str, source: str) -> None:
        with open(filename, "w") as f:
            f.write(f"{source}\n{PROGRAM_SUFFIX}")

    @staticmethod
    def _delete_file(filename: str) -> None:
        os.remove(filename)

    @staticmethod
    def _run_program(filename: str) -> subprocess.Popen:
        process = subprocess.Popen(["racket", filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process
