"""Symbolic reachability using BDDs.

This module builds a partitioned transition relation from a Petri net and
computes the set of reachable markings using symbolic fixed-point
iteration. It also exposes a BDD-based membership check for Task 4.
"""

from __future__ import annotations

import re
import time
from typing import Iterable, List, Tuple

from dd.autoref import BDD
from petri import PetriNet, parse_pnml


def _sanitize(name: str) -> str:
    """Return a BDD-safe identifier for a place name."""
    return re.sub(r"[^0-9A-Za-z_]", "_", name)


def build_reachability_bdd(net: PetriNet) -> Tuple[BDD, int, List[str]]:
    """Build BDD for Reach(M0).

    Returns:
        bdd:  BDD manager
        R:    BDD node representing the set of reachable markings
              (over current-state variables only)
        curr_vars: list of variable names for current-state places,
                   order matches net.places (bit i ↔ curr_vars[i])
    """
    bdd = BDD()

    # Declare sanitized current/next variables for each place
    bdd_vars: List[Tuple[str, str]] = []
    for i, pname in enumerate(net.places):
        base = _sanitize(pname)
        curr = f"v{i}_{base}"
        nxt = f"v{i}_{base}_next"
        bdd_vars.append((curr, nxt))

    flat_vars = [v for pair in bdd_vars for v in pair]
    bdd.declare(*flat_vars)

    rename_map = {nxt: bdd.var(curr) for curr, nxt in bdd_vars}

    # Build initial state BDD explicitly
    R = bdd.true
    for idx, (curr, _) in enumerate(bdd_vars):
        v = bdd.var(curr)
        if (net.initial >> idx) & 1:
            R = bdd.apply("and", R, v)
        else:
            R = bdd.apply("and", R, bdd.apply("not", v))

    # Build per-transition relations
    trans_bdds = []
    for t in net.transitions:
        enabled = bdd.true
        for i, (curr, _) in enumerate(bdd_vars):
            if (t.pre_mask >> i) & 1:
                enabled = bdd.apply("and", enabled, bdd.var(curr))

        relation = bdd.true
        for i, (curr, nxt) in enumerate(bdd_vars):
            is_pre = (t.pre_mask >> i) & 1
            is_post = (t.post_mask >> i) & 1

            x = bdd.var(curr)
            xnext = bdd.var(nxt)

            if is_pre and not is_post:
                # 1 -> 0
                clause = bdd.apply("and", x, bdd.apply("not", xnext))
            elif not is_pre and is_post:
                # 0 -> 1
                clause = bdd.apply("and", bdd.apply("not", x), xnext)
            elif is_pre and is_post:
                # 1 -> 1
                clause = bdd.apply("and", x, xnext)
            else:
                # unchanged: (x & x') OR (~x & ~x')
                a = bdd.apply("and", x, xnext)
                nota = bdd.apply("not", x)
                notb = bdd.apply("not", xnext)
                b = bdd.apply("and", nota, notb)
                clause = bdd.apply("or", a, b)

            relation = bdd.apply("and", relation, clause)

        trans_bdds.append(bdd.apply("and", enabled, relation))

    # Fixed-point: compute reachable states
    curr_names: Iterable[str] = [curr for curr, _ in bdd_vars]
    curr_name_set = set(curr_names)

    while True:
        R_next = bdd.false
        for tr in trans_bdds:
            inter = bdd.apply("and", R, tr)
            if inter == bdd.false:
                continue

            img = bdd.exist(curr_name_set, inter)
            img = bdd.let(rename_map, img)
            R_next = bdd.apply("or", R_next, img)

        R_new = bdd.apply("or", R, R_next)
        if R_new == R:
            break
        R = R_new

    # curr_vars: chỉ danh sách biến hiện tại, trùng thứ tự places
    curr_vars = [curr for curr, _ in bdd_vars]
    return bdd, R, curr_vars


def build_symbolic_reachability(net: PetriNet) -> int:
    """Return the number of reachable markings of a 1-safe Petri net."""
    bdd, R, curr_vars = build_reachability_bdd(net)
    return int(bdd.count(R, nvars=len(curr_vars)))


def is_marking_reachable_bdd(
    M: int, bdd: BDD, R, curr_vars: Iterable[str]
) -> bool:
    """Check if a bitmask marking M is in Reach(M0) using BDD."""
    subst = {}
    for i, var in enumerate(curr_vars):
        bit = (M >> i) & 1
        subst[var] = bdd.true if bit == 1 else bdd.false

    node = bdd.let(subst, R)
    return node == bdd.true


def main() -> None:
    filename = "pnml/philosophers.pnml"
    try:
        net = parse_pnml(filename)
    except Exception:
        net = parse_pnml("pnml/philosophers.pnml")

    print(f"Network: {filename}")
    print(f"Places: {len(net.places)}")
    print(f"Transitions: {len(net.transitions)}")

    start = time.time()
    bdd, R, curr_vars = build_reachability_bdd(net)
    count = int(bdd.count(R, nvars=len(curr_vars)))
    end = time.time()

    print("-" * 40)
    print(f"Total reachable markings: {count}")
    print(f"Time: {end - start:.4f}s")


if __name__ == "__main__":
    main()
