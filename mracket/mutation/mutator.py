"""A code mutator."""
from __future__ import annotations

import itertools
from collections.abc import Generator

from mracket import mutation
from mracket.mutation.generator import base
from mracket.reader import syntax


class Mutator(syntax.RacketASTVisitor):
    """A code mutator.

    For each node, it yields each mutation that each mutation generator generates.
    """

    def __init__(self, generators: list[base.BaseMutationGenerator]) -> None:
        self.generators = generators

    def visit(self, node: syntax.RacketASTNode) -> Generator[mutation.Mutation, None, None]:
        for generator in self.generators:
            for mut in generator.visit(node):
                yield mut
        for mut in node.accept_visitor(self):
            yield mut

    def visit_program_node(self, node: syntax.RacketProgramNode) -> Generator[mutation.Mutation, None, None]:
        for child_node in (node.reader_directive, *node.statements):
            for mut in self.visit(child_node):
                yield mut

    def visit_reader_directive_node(
        self, node: syntax.RacketReaderDirectiveNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_name_definition_node(
        self, node: syntax.RacketNameDefinitionNode
    ) -> Generator[mutation.Mutation, None, None]:
        for child_node in (node.name, node.expression):
            for mut in self.visit(child_node):
                yield mut

    def visit_structure_definition_node(
        self, node: syntax.RacketStructureDefinitionNode
    ) -> Generator[mutation.Mutation, None, None]:
        for child_node in (node.name, *node.fields):
            for mut in self.visit(child_node):
                yield mut

    def visit_literal_node(self, node: syntax.RacketLiteralNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_name_node(self, node: syntax.RacketNameNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_cond_node(self, node: syntax.RacketCondNode) -> Generator[mutation.Mutation, None, None]:
        for child_node in itertools.chain.from_iterable(node.branches):
            for mut in self.visit(child_node):
                yield mut

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> Generator[mutation.Mutation, None, None]:
        for child_node in (*node.variables, node.expression):
            for mut in self.visit(child_node):
                yield mut

    def visit_local_node(self, node: syntax.RacketLocalNode) -> Generator[mutation.Mutation, None, None]:
        for child_node in (*node.definitions, node.expression):
            for mut in self.visit(child_node):
                yield mut

    def visit_procedure_application_node(
        self, node: syntax.RacketProcedureApplicationNode
    ) -> Generator[mutation.Mutation, None, None]:
        for child_node in node.expressions:
            for mut in self.visit(child_node):
                yield mut

    def visit_test_case_node(self, node: syntax.RacketTestCaseNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_library_require_node(
        self, node: syntax.RacketLibraryRequireNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield
