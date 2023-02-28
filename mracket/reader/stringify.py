"""Stringify a Racket abstract syntax tree."""
from __future__ import annotations

from mracket.reader import syntax


class Stringifier(syntax.RacketASTVisitor):
    """Stringifier of a Racket abstract syntax tree."""

    def visit_program_node(self, node: syntax.RacketProgramNode) -> str:
        return self.visit(node.reader_directive) + "\n" + "\n".join(map(self.visit, node.statements))

    def visit_reader_directive_node(self, node: syntax.RacketReaderDirectiveNode) -> str:
        return node.token.source

    def visit_name_definition_node(self, node: syntax.RacketNameDefinitionNode) -> str:
        return f"(define {node.name.token.source} {self.visit(node.expression)})"

    def visit_structure_definition_node(self, node: syntax.RacketStructureDefinitionNode) -> str:
        return f"(define-struct {node.name} ({' '.join(map(self.visit, node.fields))}))"

    def visit_literal_node(self, node: syntax.RacketLiteralNode) -> str:
        return node.token.source

    def visit_name_node(self, node: syntax.RacketNameNode) -> str:
        return node.token.source

    def visit_cond_node(self, node: syntax.RacketCondNode) -> str:
        branches = " ".join(
            f"({self.visit(condition)} {self.visit(expression)})" for condition, expression in node.branches
        )
        return f"(cond {branches})"

    def visit_lambda_node(self, node: syntax.RacketLambdaNode) -> str:
        return f"(lambda ({' '.join(map(self.visit, node.variables))}) {self.visit(node.expression)})"

    def visit_let_node(self, node: syntax.RacketLetNode) -> str:
        local_definitions = " ".join(
            f"({self.visit(name)} {self.visit(expression)})" for name, expression in node.local_definitions
        )
        return f"({node.type.value} ({local_definitions}) {self.visit(node.expression)})"

    def visit_local_node(self, node: syntax.RacketLocalNode) -> str:
        return f"(local ({' '.join(map(self.visit, node.definitions))}) {self.visit(node.expression)})"

    def visit_procedure_application_node(self, node: syntax.RacketProcedureApplicationNode) -> str:
        return f"({' '.join(map(self.visit, node.expressions))})"

    def visit_test_case_node(self, node: syntax.RacketTestCaseNode) -> str:
        return f"({node.type.value} {' '.join(map(self.visit, node.expressions))})"

    def visit_library_require_node(self, node: syntax.RacketLibraryRequireNode) -> str:
        return f"(require {self.visit(node.library)})"
