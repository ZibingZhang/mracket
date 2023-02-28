"""A code mutation applier."""
from __future__ import annotations

import itertools
from collections.abc import Generator
from typing import Any, cast

from mracket import mutation
from mracket.reader import stringify, syntax


class MutationApplier(syntax.RacketASTVisitor):
    """Applies mutations to the program.

    For each node of the program, if there exists a mutation where that node is
    replaced, it replaces the node and yields a stringified version of the entire
    program with the updated node. The node is then swapped back.
    """

    stringifier: stringify.Stringifier = stringify.Stringifier()

    def __init__(self, program: syntax.RacketProgramNode, mutations: list[mutation.Mutation]):
        self.program = program
        self.mutations = mutations

    def apply_mutations(self) -> Generator[tuple[mutation.Mutation, str], None, None]:
        for result in self.visit(self.program):
            yield result

    def visit_program_node(
        self, node: syntax.RacketProgramNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        reader_directive = node.reader_directive
        for mut in self._get_mutations(node.reader_directive):
            node.reader_directive = cast(syntax.RacketReaderDirectiveNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.reader_directive = reader_directive

        statements = node.statements.copy()
        for i, statement in enumerate(node.statements):
            for mut in self._get_mutations(statement):
                node.statements[i] = cast(syntax.RacketStatementNode, mut.replacement)
                yield mut, self.stringifier.visit(self.program)
            node.statements = statements

        for child_node in [node.reader_directive, *node.statements]:
            for result in self.visit(child_node):
                yield result

    def visit_reader_directive_node(
        self, node: syntax.RacketReaderDirectiveNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        return
        yield

    def visit_name_definition_node(
        self, node: syntax.RacketNameDefinitionNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        name = node.name
        for mut in self._get_mutations(node.name):
            node.name = cast(syntax.RacketNameNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.name = name

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.expression = expression

        for child_node in [node.name, node.expression]:
            for result in self.visit(child_node):
                yield result

    def visit_structure_definition_node(
        self, node: syntax.RacketStructureDefinitionNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        name = node.name
        for mut in self._get_mutations(node.name):
            node.name = cast(syntax.RacketNameNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.name = name

        fields = node.fields.copy()
        for i, field in enumerate(node.fields):
            for mut in self._get_mutations(field):
                node.fields[i] = cast(syntax.RacketNameNode, mut.replacement)
                yield mut, self.stringifier.visit(self.program)
            node.fields = fields

        for child_node in [node.name, *node.fields]:
            for result in self.visit(child_node):
                yield result

    def visit_literal_node(
        self, node: syntax.RacketLiteralNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        return
        yield

    def visit_name_node(self, node: syntax.RacketNameNode) -> Generator[tuple[mutation.Mutation, str], None, None]:
        return
        yield

    def visit_cond_node(self, node: syntax.RacketCondNode) -> Generator[tuple[mutation.Mutation, str], None, None]:
        branches = node.branches.copy()
        for i, (condition, expression) in enumerate(node.branches):
            for mut in self._get_mutations(condition):
                node.branches[i] = (cast(syntax.RacketExpressionNode, mut.replacement), node.branches[i][1])
            node.branches = branches

            for mut in self._get_mutations(expression):
                node.branches[i] = (node.branches[i][0], cast(syntax.RacketExpressionNode, mut.replacement))
            node.branches[i] = (condition, expression)

        for child_node in itertools.chain.from_iterable(node.branches):
            for result in self.visit(child_node):
                yield result

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> Generator[tuple[mutation.Mutation, str], None, None]:
        variables = node.variables.copy()
        for i, variable in enumerate(node.variables):
            for mut in self._get_mutations(variable):
                node.variables[i] = cast(syntax.RacketNameNode, mut.replacement)
            node.variables = variables

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.expression = expression

        for child_node in [*node.variables, node.expression]:
            for result in self.visit(child_node):
                yield result

    def visit_local_node(self, node: syntax.RacketLocalNode) -> Any:
        definitions = node.definitions.copy()
        for i, definition in enumerate(node.definitions):
            for mut in self._get_mutations(definition):
                node.definitions[i] = cast(syntax.RacketDefinitionNode, mut.replacement)
            node.definitions = definitions

        expression = node.expression
        for mut in self._get_mutations(node.expression):
            node.expression = cast(syntax.RacketExpressionNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.expression = expression

        for child_node in [*node.definitions, node.expression]:
            for result in self.visit(child_node):
                yield result

    def visit_procedure_application_node(
        self, node: syntax.RacketProcedureApplicationNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        expressions = node.expressions.copy()
        for i, expression in enumerate(node.expressions):
            for mut in self._get_mutations(expression):
                node.expressions[i] = cast(syntax.RacketExpressionNode, mut.replacement)
                yield mut, self.stringifier.visit(self.program)
            node.expressions = expressions

        for child_node in node.expressions:
            for result in self.visit(child_node):
                yield result

    def visit_test_case_node(
        self, node: syntax.RacketTestCaseNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        expressions = node.expressions.copy()
        for i, expression in enumerate(node.expressions):
            for mut in self._get_mutations(expression):
                node.expressions[i] = cast(syntax.RacketExpressionNode, mut.replacement)
                yield mut, self.stringifier.visit(self.program)
            node.expressions = expressions

        for child_node in node.expressions:
            for result in self.visit(child_node):
                yield result

    def visit_library_require_node(
        self, node: syntax.RacketLibraryRequireNode
    ) -> Generator[tuple[mutation.Mutation, str], None, None]:
        library = node.library
        for mut in self._get_mutations(node.library):
            node.library = cast(syntax.RacketNameNode, mut.replacement)
            yield mut, self.stringifier.visit(self.program)
        node.library = library

        for result in self.visit(library):
            yield result

    def _get_mutations(self, node: syntax.RacketASTNode) -> Generator[mutation.Mutation, None, None]:
        for mut in self.mutations:
            if node is mut.original:
                yield mut
