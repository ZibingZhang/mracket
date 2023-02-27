"""A code mutation."""
from __future__ import annotations

import dataclasses

from mracket.reader import syntax


@dataclasses.dataclass(frozen=True)
class Mutation:
    original: syntax.RacketASTNode
    replacement: syntax.RacketASTNode
    explanation: str
