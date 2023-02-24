"""Stringify a Racket AST."""
from __future__ import annotations

from typing import Any

from mracket.reader import syntax


class StringifyVisitor(syntax.RacketASTVisitor):
    def visit_program_node(self, node: syntax.RacketProgramNode) -> Any:
        return self.visit(node.reader_directive) + "\n" + "\n".join(map(self.visit, node.statements))

    def visit_reader_directive_node(self, node: syntax.RacketReaderDirectiveNode) -> Any:
        return node.token.source

    def visit_constant_definition_node(self, node: syntax.RacketConstantDefinitionNode) -> Any:
        return f"(define {node.name.source} {self.visit(node.expression)})"

    def visit_structure_definition_node(self, node: syntax.RacketStructureDefinitionNode) -> Any:
        return f"(define-struct {node.name} ({' '.join(map(self.visit, node.fields))}))"

    def visit_boolean_node(self, node: syntax.RacketBooleanNode) -> Any:
        return node.token.source

    def visit_character_node(self, node: syntax.RacketCharacterNode) -> Any:
        return node.token.source

    def visit_name_node(self, node: syntax.RacketNameNode) -> Any:
        return node.token.source

    def visit_number_node(self, node: syntax.RacketNumberNode) -> Any:
        return node.token.source

    def visit_string_node(self, node: syntax.RacketStringNode) -> Any:
        return node.token.source

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> Any:
        return f"(lambda ({' '.join(map(self.visit, node.variables))}) {self.visit(node.expression)})"

    def visit_procedure_application_node(self, node: syntax.RacketProcedureApplicationNode) -> Any:
        pass

    def visit_check_expect_node(self, node: syntax.RacketCheckExpectNode) -> Any:
        pass

    def visit_library_require_node(self, node: syntax.RacketLibraryRequireNode) -> Any:
        pass
