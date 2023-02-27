"""A code mutator."""
from __future__ import annotations

from typing import Generator

from mracket import mutation
from mracket.mutation.generator import base
from mracket.reader import syntax


class Mutator(syntax.RacketASTVisitor):
    def __init__(self, generators: list[base.BaseMutationGenerator]) -> None:
        self.generators = generators

    def visit(self, node: syntax.RacketASTNode) -> Generator[mutation.Mutation, None, None]:
        for generator in self.generators:
            for mut in generator.visit(node):
                yield mut
        for mut in node.accept_visitor(self):
            yield mut

    def visit_program_node(self, node: syntax.RacketProgramNode) -> Generator[mutation.Mutation, None, None]:
        for mut in self.visit(node.reader_directive):
            yield mut
        for statement in node.statements:
            for mut in self.visit(statement):
                yield mut

    def visit_reader_directive_node(
        self, node: syntax.RacketReaderDirectiveNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_constant_definition_node(
        self, node: syntax.RacketConstantDefinitionNode
    ) -> Generator[mutation.Mutation, None, None]:
        for mut in self.visit(node.name):
            yield mut
        for mut in self.visit(node.expression):
            yield mut

    def visit_structure_definition_node(
        self, node: syntax.RacketStructureDefinitionNode
    ) -> Generator[mutation.Mutation, None, None]:
        for mut in self.visit(node.name):
            yield mut
        for field in node.fields:
            for mut in self.visit(field):
                yield mut

    def visit_literal_node(self, node: syntax.RacketLiteralNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_name_node(self, node: syntax.RacketNameNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> Generator[mutation.Mutation, None, None]:
        for variable in node.variables:
            for mut in self.visit(variable):
                yield mut
        for mut in self.visit(node.expression):
            yield mut

    def visit_procedure_application_node(
        self, node: syntax.RacketProcedureApplicationNode
    ) -> Generator[mutation.Mutation, None, None]:
        for expression in node.expressions:
            for mut in self.visit(expression):
                yield mut

    def visit_check_expect_node(self, node: syntax.RacketCheckExpectNode) -> Generator[mutation.Mutation, None, None]:
        return
        yield

    def visit_library_require_node(
        self, node: syntax.RacketLibraryRequireNode
    ) -> Generator[mutation.Mutation, None, None]:
        return
        yield
