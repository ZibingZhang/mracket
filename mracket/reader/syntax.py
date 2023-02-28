"""Abstract syntax tree defition for Racket programs."""
from __future__ import annotations

import abc
from typing import Any

from mracket.reader import lexer


class RacketASTVisitor(metaclass=abc.ABCMeta):
    """A Racket AST visitor."""

    def visit(self, node: RacketASTNode) -> Any:
        return node.accept_visitor(self)

    @abc.abstractmethod
    def visit_program_node(self, node: RacketProgramNode) -> Any:
        """Visit a program node.

        :param node: A program node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_reader_directive_node(self, node: RacketReaderDirectiveNode) -> Any:
        """Visit a reader directive node.

        :param node: A reader directive node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_name_definition_node(self, node: RacketNameDefinitionNode) -> Any:
        """Visit a name definition node.

        :param node: A name definition node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_structure_definition_node(self, node: RacketStructureDefinitionNode) -> Any:
        """Visit a structure definition node.

        :param node: A structure definition node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_literal_node(self, node: RacketLiteralNode) -> Any:
        """Visit a literal node.

        :param node: A literal node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_name_node(self, node: RacketNameNode) -> Any:
        """Visit a name node.

        :param node: A name node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_cond_node(self, node: RacketCondNode) -> Any:
        """Visit a cond node.

        :param node: A cond node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_lambda_node(self, node: RacketLambdaNode) -> Any:
        """Visit a lambda node.

        :param node: A lambda node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_local_node(self, node: RacketLocalNode) -> Any:
        """Visit a local node.

        :param node: A local node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_procedure_application_node(self, node: RacketProcedureApplicationNode) -> Any:
        """Visit a procedure application node.

        :param node: A procedure node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_check_expect_node(self, node: RacketCheckExpectNode) -> Any:
        """Visit a check expect node.

        :param node: A check expect node
        :return: The result of the visitor visiting this node
        """

    @abc.abstractmethod
    def visit_library_require_node(self, node: RacketLibraryRequireNode) -> Any:
        """Visit a library require node.

        :param node: A library require node
        :return: The result of the visitor visiting this node
        """


class RacketASTNode(metaclass=abc.ABCMeta):
    """An AST node."""

    def __init__(self, token: lexer.Token) -> None:
        self.token = token

    @abc.abstractmethod
    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        """Accept a Racket AST visitor.

        :param visitor: A Racket AST visitor
        :return: The result of the visitor visiting this node
        """


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

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, name: RacketNameNode) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen
        self.name = name


class RacketNameDefinitionNode(RacketDefinitionNode):
    """A name definition node."""

    def __init__(
        self, lparen: lexer.Token, rparen: lexer.Token, name: RacketNameNode, expression: RacketExpressionNode
    ):
        super().__init__(lparen, rparen, name)
        self.expression = expression

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_name_definition_node(self)


class RacketStructureDefinitionNode(RacketDefinitionNode):
    """A structure definition node."""

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, name: RacketNameNode, fields: list[RacketNameNode]):
        super().__init__(lparen, rparen, name)
        self.fields = fields

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_structure_definition_node(self)


class RacketExpressionNode(RacketStatementNode, metaclass=abc.ABCMeta):
    """An expression node."""


class RacketLiteralNode(RacketExpressionNode):
    """A literal."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_literal_node(self)


class RacketNameNode(RacketExpressionNode):
    """A name node."""

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_name_node(self)


class RacketSExprNode(RacketExpressionNode, metaclass=abc.ABCMeta):
    """An s-expression node.

    Starts with a left parenthesis and ends with a right parenthesis.
    """

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen


class RacketCondNode(RacketSExprNode):
    """A cond node."""

    def __init__(
        self,
        lparen: lexer.Token,
        rparen: lexer.Token,
        branches: list[tuple[RacketExpressionNode, RacketExpressionNode]],
    ) -> None:
        super().__init__(lparen, rparen)
        self.branches = branches

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_cond_node(self)


class RacketLambdaNode(RacketSExprNode):
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


class RacketLocalNode(RacketSExprNode):
    """A local node."""

    def __init__(
        self,
        lparen: lexer.Token,
        rparen: lexer.Token,
        definitions: list[RacketDefinitionNode],
        expression: RacketExpressionNode,
    ) -> None:
        super().__init__(lparen, rparen)
        self.definitions = definitions
        self.expression = expression

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_local_node(self)


class RacketProcedureApplicationNode(RacketSExprNode):
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

    def __init__(self, lparen: lexer.Token, rparen: lexer.Token, library: RacketNameNode) -> None:
        super().__init__(lparen)
        self.lparen = lparen
        self.rparen = rparen
        self.library = library

    def accept_visitor(self, visitor: RacketASTVisitor) -> Any:
        return visitor.visit_library_require_node(self)
