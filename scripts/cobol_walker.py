#!/usr/bin/env python3
"""
cobol_walker.py — Deterministic execution-order traversal over CobolProgramDict.

Implements CobolWalker v0.1 exactly per SPEC-CobolWalker.md (approved 2026-05-18,
commit 450059a).

Key contract:
- Constructor takes a CobolProgramDict (the single source of truth).
- walk(include_dead_code: bool = False) yields paragraph names in deterministic
  DFS pre-order visit order.
- Starts at prog.entry_paragraph.
- For any paragraph, children are visited in this order:
    1. All targets in its "performs" list (exact order from the canonical IR)
    2. Its "falls_through_to" target (if present and non-null)
- Fully cycle-safe via visited set: each paragraph is yielded at most once,
  the first time it is discovered.
- include_dead_code=False (default): only paragraphs reachable via the above
  traversal from entry.
- include_dead_code=True: the live set above, followed by any remaining
  paragraphs (the IR's dead_code_paragraphs) appended in canonical source order.

This is a pure consumer. It never reads files or calls extractors.

See SPEC-CobolWalker.md for the 10 acceptance gates, especially Gate 3
(live corpus count must equal 205) and Gate 4 (full count must equal 518).
"""

from __future__ import annotations

from collections.abc import Generator

from scripts.cobol_program_dict import CobolProgramDict


class CobolWalker:
    """
    Cycle-safe deterministic walker for COBOL paragraph execution order.

    Example:
        from scripts.cobol_program_dict import CobolProgramDict
        from scripts.cobol_walker import CobolWalker

        prog = CobolProgramDict("CBACT01C")
        walker = CobolWalker(prog)

        for para in walker.walk():
            print(para)                    # live paragraphs only

        for para in walker.walk(include_dead_code=True):
            print(para)                    # live + dead in source order
    """

    def __init__(self, prog: CobolProgramDict):
        if not isinstance(prog, CobolProgramDict):
            raise TypeError(
                f"CobolWalker requires CobolProgramDict, got {type(prog).__name__}"
            )
        self.prog: CobolProgramDict = prog

    def walk(self, include_dead_code: bool = False) -> Generator[str, None, None]:
        """
        Yield paragraph names in DFS pre-order starting from entry_paragraph.

        Traversal rule (per SPEC):
        - Begin at prog.entry_paragraph
        - From any paragraph P, follow:
            1. P["performs"] targets in the exact order stored in the IR
            2. P["falls_through_to"] (singular, if non-null)
        - Yield a paragraph exactly once, at the moment of first discovery.
        - Visited set guarantees termination on cycles.
        """
        paragraphs = self.prog.paragraphs
        entry = self.prog.entry_paragraph

        if not entry or entry not in paragraphs:
            return

        visited: set[str] = set()
        # Iterative DFS stack. Push children reversed so first child is next.
        stack: list[str] = [entry]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)
            yield current

            record = paragraphs[current]
            children: list[str] = []

            # 1. performs targets — preserve exact order from IR
            for target in record.get("performs", []) or []:
                if target not in children and target in paragraphs:
                    children.append(target)

            # 2. falls_through_to (after all performs)
            ft = record.get("falls_through_to")
            if ft and ft not in children and ft in paragraphs:
                children.append(ft)

            # Push reversed for correct DFS pre-order
            for child in reversed(children):
                if child not in visited:
                    stack.append(child)

        if include_dead_code:
            # Append unreached paragraphs in canonical source order
            for name in paragraphs:
                if name not in visited:
                    yield name

    def __repr__(self) -> str:
        return (
            f"<CobolWalker {self.prog.name} "
            f"entry={self.prog.entry_paragraph!r} "
            f"paragraphs={len(self.prog.paragraphs)}>"
        )


# ----------------------------------------------------------------------
# Quick manual verification (not part of the public API)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    prog_name = sys.argv[1] if len(sys.argv) > 1 else "CBACT01C"
    prog = CobolProgramDict(prog_name)
    walker = CobolWalker(prog)

    live = list(walker.walk(include_dead_code=False))
    full = list(walker.walk(include_dead_code=True))

    print(f"Program: {prog.name}")
    print(f"Entry (CFG root): {prog.entry_paragraph}")
    print(f"Paragraphs in IR: {len(prog.paragraphs)}")
    print(f"Live via walk(False): {len(live)}")
    print(f"Full via walk(True):  {len(full)}")
    print(f"First 5 live: {live[:5]}")
    if full:
        print(f"Last 3 full : {full[-3:]}")
    print("OK")