"""AST for Racket."""
from __future__ import annotations

import abc
from typing import Any

from mracket.reader import lexer

__all__ = [
    "RacketProgramNode",
    "RacketReaderDirectiveNode",
    "RacketConstantDefinitionNode",
    "RacketStructureDefinitionNode",
    "RacketBooleanNode",
    "RacketCharacterNode",
    "RacketNameNode",
    "RacketNumberNode",
    "RacketStringNode",
    "RacketLambdaNode",
    "RacketProcedureApplicationNode",
    "RacketCheckExpectNode",
    "RacketLibraryRequireNode",
]


class RacketASTVisitor(metaclass=abc.ABCMeta):
    """A Racket AST visitor."""

    def visit(self, node: RacketASTNode) -> Any:
        return node.accept_visitor(self)

    @abc.abstractmethod
    def visit_program_node(self, node: RacketProgramNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_reader_directive_node(self, node: RacketReaderDirectiveNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_constant_definition_node(self, node: RacketConstantDefinitionNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_structure_definition_node(self, node: RacketStructureDefinitionNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_boolean_node(self, node: RacketBooleanNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_character_node(self, node: RacketCharacterNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_name_node(self, node: RacketNameNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_number_node(self, node: RacketNumberNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_string_node(self, node: RacketStringNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_lambda_node(self, node: RacketLambdaNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_procedure_application_node(self, node: RacketProcedureApplicationNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_check_expect_node(self, node: RacketCheckExpectNode) -> Any:
        ...

    @abc.abstractmethod
    def visit_library_require_node(self, node: RacketLibraryRequireNode) -> Any:
        ...


class RacketASTNode(metaclass=abc.ABCMeta):
    """An AST node."""

    def __init__(self, token: lexer.Token) -> None:
        self.token = token

    @abc.abstractmethod
    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        pass


class RacketProgramNode(RacketASTNode):
    """A program node."""

    def __init__(
        self, token: lexer.Token, reader_directive: RacketReaderDirectiveNode, statements: list[RacketStatementNode]
    ) -> None:
        super().__init__(token)
        self.reader_directive = reader_directive
        self.statements = statements

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_program_node(self)


class RacketReaderDirectiveNode(RacketASTNode):
    """A reader directive node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_reader_directive_node(self)


class RacketStatementNode(RacketASTNode, metaclass=abc.ABCMeta):
    """A statement node."""


class RacketDefinitionNode(RacketStatementNode, metaclass=abc.ABCMeta):
    """A definition node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, name: lexer.Token) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen
        self.name = name


class RacketConstantDefinitionNode(RacketDefinitionNode):
    """A constant definition node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, name: lexer.Token, expression: RacketExpressionNode):
        super().__init__(lparen, rparen, name)
        self.expression = expression

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_constant_definition_node(self)


class RacketStructureDefinitionNode(RacketDefinitionNode):
    """A structure definition node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, name: lexer.Token, fields: list[RacketNameNode]):
        super().__init__(lparen, rparen, name)
        self.fields = fields

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_structure_definition_node(self)


class RacketExpressionNode(RacketStatementNode, metaclass=abc.ABCMeta):
    """An expression node."""


class RacketAtomicNode(RacketExpressionNode, metaclass=abc.ABCMeta):
    """An atomic node.

    Does not contain any parentheses.
    """


class RacketBooleanNode(RacketAtomicNode):
    """A boolean node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_boolean_node(self)


class RacketCharacterNode(RacketAtomicNode):
    """A character node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_character_node(self)


class RacketNameNode(RacketAtomicNode):
    """A name node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_name_node(self)


class RacketNumberNode(RacketAtomicNode):
    """A number node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_number_node(self)


class RacketStringNode(RacketAtomicNode):
    """A string node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_string_node(self)


class RacketComplexNode(RacketExpressionNode, metaclass=abc.ABCMeta):
    """A complex node.

    Starts with a left parenthesis and ends with a right parenthesis.
    """

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen


class RacketLambdaNode(RacketComplexNode):
    """A lambda node."""

    def __init__(
        self,
        lparen: lexer.Token,
        rparen: lexer.Token,
        variables: list[RacketNameNode],
        expression: RacketExpressionNode,
    ) -> None:
        super().__init__(lparen, rparen)
        self.variables = variables
        self.expression = expression

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_lambda_node(self)


class RacketProcedureApplicationNode(RacketComplexNode):
    """A procedure application node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, expressions: list[RacketExpressionNode]) -> None:
        super().__init__(lparen, rparen)
        self.expressions = expressions

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_procedure_application_node(self)


class RacketTestCaseNode(RacketStatementNode, metaclass=abc.ABCMeta):
    """A test case node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen


class RacketCheckExpectNode(RacketTestCaseNode):
    """A check-expect node."""

    def __init__(
        self, lparen: lexer.Token, rparen: lexer.Token, actual: RacketExpressionNode, expected: RacketExpressionNode
    ) -> None:
        super().__init__(lparen, rparen)
        self.actual = actual
        self.expected = expected

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_check_expect_node(self)


class RacketLibraryRequireNode(RacketStatementNode):
    """A library require node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, library: lexer.Token) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen
        self.library = library

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_library_require_node(self)
