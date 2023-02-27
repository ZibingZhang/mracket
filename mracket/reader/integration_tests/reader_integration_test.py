"""Integration tests for mracket.reader."""
from __future__ import annotations

import subprocess
import tempfile

import pytest

from mracket import test
from mracket.reader.lexer import Lexer
from mracket.reader.parser import Parser
from mracket.reader.stringify import Stringifier


def test_read_program_succeeds() -> None:
    for source in test.inputs.read_contents():
        tokens = Lexer(source).tokenize()
        Parser(tokens).parse()


def test_read_stringify_idempotent() -> None:
    for source in test.inputs.read_contents():
        tokens_0 = Lexer(source).tokenize()
        tree_0 = Parser(tokens_0).parse()
        stringified_tree_0 = Stringifier().visit(tree_0)

        tokens_1 = Lexer(stringified_tree_0).tokenize()
        tree_1 = Parser(tokens_1).parse()
        stringified_tree_1 = Stringifier().visit(tree_1)

        assert stringified_tree_0 == stringified_tree_1


@pytest.mark.slow
def test_racket_output_unchanged() -> None:
    for file_name in test.inputs.file_names():
        original_process = subprocess.Popen(["racket", file_name], stdout=subprocess.PIPE)

        with open(file_name) as f:
            source = f.read()
        tokens = Lexer(source).tokenize()
        tree = Parser(tokens).parse()
        stringified_tree = Stringifier().visit(tree)

        with tempfile.NamedTemporaryFile(mode="w") as tf:
            tf.write(stringified_tree)

        transformed_process = subprocess.Popen(["racket", tf.name], stdout=subprocess.PIPE)

        (original_output, original_error) = original_process.communicate()
        (transformed_output, transformed_error) = transformed_process.communicate()

        assert original_process.returncode == transformed_process.returncode
        if original_error is None:
            assert original_output == transformed_output
