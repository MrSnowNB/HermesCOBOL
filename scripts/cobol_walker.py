#!/usr/bin/env python3
"""
cobol_walker.py — Deterministic execution-order traversal over CobolProgramDict.

Implements CobolWalker v0.1 per SPEC-CobolWalker.md (approved 2026-05-18).

Contract:
- Constructor accepts a CobolProgramDict.
- walk(include_dead_code: bool = False) is a generator yielding paragraph names
  in DFS pre-order visit sequence starting from entry_paragraph.
- Traversal follows performs (in listed order) then falls_through_to.
- Cycle-safe via visited set (each paragraph yielded at most once).
- When include_dead_code=False: only the paragraphs discovered by the traversal.
- When include_dead_code=True: discovered paragraphs followed by any remaining
  paragraphs (the IR's dead_code_paragraphs) in source order.

This module is a pure consumer of CobolProgramDict. It does not read files
or call any extractors directly.

See SPEC-CobolWalker.md for the full 10-gate acceptance criteria.
"""

from __future__ import annotations

from collections import deque
from typing import Generator

from scripts.cobol_program_dict import CobolProgramDict


class CobolWalker:
    """
    Cycle-safe, deterministic walker that yields paragraphs in execution/visit order.

    Usage:
        prog = CobolProgramDict("CBACT01C")
        walker = CobolWalker(prog)
        for para in walker.walk():
            ...
        for para in walker.walk(include_dead_code=True):
            ...
    """

    def __init__(self, prog: CobolProgramDict):
        if not isinstance(prog, CobolProgramDict):
            raise TypeError(
                f"CobolWalker requires a CobolProgramDict instance, got {type(prog)}"
            )
        self.prog: CobolProgramDict = prog
        self._entry: str = prog.entry_paragraph
        self._paras: dict[str, dict] = prog.paragraphs  # name -> record

    def walk(self, include_dead_code: bool = False) -> Generator[str, None, None]:
        """
        Yield paragraph names in DFS pre-order starting from entry_paragraph.

        Traversal order for the children of any paragraph P:
          1. Every target in P["performs"] (in the exact order stored in the canonical IR)
          2. P["falls_through_to"] (if non-null)

        A paragraph is yielded exactly once, the first time it is discovered.
        """
        if not self._entry or self._entry not in self._paras:
            return  # empty program — yield nothing

        visited: set[str] = set()
        # Use a stack for explicit DFS pre-order (append/pop for LIFO)
        # Each stack entry is the paragraph name to visit next.
        stack: list[str] = [self._entry]

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            yield current

            # Get children in the exact required order
            record = self._paras.get(current, {})
            children: list[str] = []

            # 1. performs targets (preserve order, dedup just in case)
            for target in record.get("performs", []) or []:
                if target not in children:
                    children.append(target)

            # 2. falls_through_to (singular)
            ft = record.get("falls_through_to")
            if ft and ft not in children:
                children.append(ft)

            # Push children in reverse so that the first child is processed next (DFS pre-order)
            for child in reversed(children):
                if child in self._paras and child not in visited:
                    stack.append(child)

        if include_dead_code:
            # Append any paragraphs that were never visited, in source order
            for name in self.prog.paragraphs:  # paragraphs is an OrderedDict-like in insertion order
                if name not in visited:
                    yield name

    def __repr__(self) -> str:
        return f"<CobolWalker {self.prog.name} entry={self._entry!r}>"


# ----------------------------------------------------------------------
# Minimal smoke test / manual verification (run directly)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    prog_name = sys.argv[1] if len(sys.argv) > 1 else "CBACT01C"
    prog = CobolProgramDict(prog_name)
    walker = CobolWalker(prog)

    live = list(walker.walk(include_dead_code=False))
    full = list(walker.walk(include_dead_code=True))

    print(f"Program: {prog.name}")
    print(f"Entry:   {prog.entry_paragraph}")
    print(f"Total paragraphs in IR: {len(prog.paragraphs)}")
    print(f"Live via walk(False):   {len(live)}")
    print(f"Full via walk(True):    {len(full)}")
    print(f"First 5 (live): {live[:5]}")
    print(f"Last 3 (full):  {full[-3:]}")
    print("OK")