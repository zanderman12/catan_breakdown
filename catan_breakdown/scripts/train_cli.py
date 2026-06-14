#!/usr/bin/env python3
"""Interactive Catan settlement placement training tool."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from catan.board import CatanBoard, NODE_COORDS
from catan.scoring import score_placement, percentile_rank
from catan.recommender import recommend


_RES_ABBREV = {
    'wood': 'WD', 'brick': 'BK', 'ore': 'OR',
    'sheep': 'SH', 'wheat': 'WH', 'desert': '--',
}

_PORT_LABEL = {
    'wood': 'WD 2:1', 'brick': 'BK 2:1', 'ore': 'OR 2:1',
    'sheep': 'SH 2:1', 'wheat': 'WH 2:1', 'any': '3:1  ',
}

# Tile indices grouped by board row (3-4-5-4-3 spiral layout)
_TILE_ROWS = [range(0, 3), range(3, 7), range(7, 12), range(12, 16), range(16, 19)]


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"


def render_board(board: CatanBoard, placed: list[int], valid: list[int]) -> None:
    """Print ASCII hex board. Each node is [nn]=valid, (nn)=placed, ' nn '=invalid."""
    placed_set = set(placed)
    valid_set = set(valid)

    # Group nodes by row number from NODE_COORDS
    rows: dict[int, list[tuple[int, int]]] = {}
    for node, (col, row) in NODE_COORDS.items():
        rows.setdefault(row, []).append((col, node))

    COL_SCALE = 4
    COL_OFFSET = 2  # shifts minimum col (-2) to x=0
    canvas_width = (19 + COL_OFFSET) * COL_SCALE + 5

    print()
    for row_idx in range(6):
        line = [' '] * canvas_width
        for col, node in sorted(rows[row_idx]):
            x = (col + COL_OFFSET) * COL_SCALE
            if node in placed_set:
                cell = f'({node:2d})'
            elif node in valid_set:
                cell = f'[{node:2d}]'
            else:
                cell = f' {node:2d} '
            for i, ch in enumerate(cell):
                if x + i < len(line):
                    line[x + i] = ch
        print(''.join(line).rstrip())

    # Tile legend in hex-shaped rows (3-4-5-4-3)
    tile_dict = board.tile_dict
    TILE_SLOT_W = 9  # "[WD/ 6]" = 7 chars + 2-char separator
    print()
    print("Board tiles:")
    for t_row in _TILE_ROWS:
        tiles = list(t_row)
        indent = " " * ((5 - len(tiles)) * TILE_SLOT_W // 2)
        parts = []
        for t in tiles:
            res = tile_dict[t]['resource']
            num = tile_dict[t]['num']
            abbr = _RES_ABBREV[res]
            parts.append(f"[{abbr}/{num:2d}]" if num else f"[{abbr}/--]")
        print(indent + "  ".join(parts))

    # Port legend
    ports: dict[str, list[int]] = {}
    for node, data in board.settlement_dict.items():
        if data['port']:
            label = _PORT_LABEL[data['port']]
            ports.setdefault(label, []).append(node)
    if ports:
        print()
        print("Ports:")
        for label in sorted(ports):
            node_str = ", ".join(str(n) for n in sorted(ports[label]))
            print(f"  {label}: nodes {node_str}")
    print()


def _score_table(sc: dict) -> str:
    return "\n".join([
        f"  Pips           {sc['pips']:6d}",
        f"  Resource score {sc['resource_score']:9.2f}",
        f"  Port value     {sc['port_value']:9.2f}",
        f"  Diversity      {sc['diversity_score']:9.2f}",
        f"  Port synergy   {sc['port_synergy']:9.2f}",
        f"  {'─' * 25}",
        f"  Composite      {sc['composite_score']:9.2f}",
    ])


def print_placement_feedback(
    pick_num: int,
    node: int,
    placed: list[int],
    board: CatanBoard,
    pre_recs: list[tuple[int, float]],
) -> None:
    """Print score breakdown, best available, percentile, and top-3 alternatives."""
    user_sc = score_placement(placed, board)
    pctile = percentile_rank(placed, board, n_simulations=1000)

    # Best available was the #1 recommendation before the pick
    before = placed[:-1]
    if pre_recs:
        top_node = pre_recs[0][0]
        best_composite = score_placement(before + [top_node], board)['composite_score']
    else:
        top_node = node
        best_composite = user_sc['composite_score']

    print(f"\nPlaced settlement {pick_num} at node {node}\n")
    print("Score breakdown:")
    print(_score_table(user_sc))
    print()

    if top_node == node:
        print(f"Best available composite: {best_composite:.2f}  (your choice was optimal!)")
    else:
        print(f"Best available composite: {best_composite:.2f}  (node {top_node})")

    print(f"Percentile rank: {_ordinal(round(pctile))} (vs 1000 random placements)")

    # Top-3 alternatives (filter out user's pick)
    alts = [(n, s) for n, s in pre_recs if n != node]
    if alts:
        print("\nTop-3 alternatives:")
        for rank, (alt_n, _) in enumerate(alts[:3], 1):
            alt_sc = score_placement(before + [alt_n], board)
            print(f"  {rank}. Node {alt_n:2d}: {alt_sc['composite_score']:.2f}")


def print_summary(placed: list[int], board: CatanBoard) -> None:
    """Full summary after both settlements are placed."""
    sc = score_placement(placed, board)
    pctile = percentile_rank(placed, board, n_simulations=1000)

    print("\n" + "═" * 44)
    print("        SETTLEMENT SUMMARY")
    print("═" * 44)
    print(f"Your settlements: nodes {placed[0]} and {placed[1]}")
    print()
    print("Score breakdown:")
    print(_score_table(sc))
    print()
    print(
        f"Overall percentile: {_ordinal(round(pctile))}"
        f" (vs 1000 random 2-settlement placements)"
    )

    # Resources by roll number across both settlements
    res_by_num: dict[int, list[str]] = {}
    for node in placed:
        for num, res in board.settlement_dict[node]['numres']:
            if num != 0:
                pip = board.pipdict[num]
                res_by_num.setdefault(num, []).append(f"{res}({pip}{'pip' if pip == 1 else 'pips'})")
    if res_by_num:
        print()
        print("Resources by roll:")
        for num in sorted(res_by_num):
            print(f"  Roll {num:2d} → {', '.join(res_by_num[num])}")

    # Starting hand from 2nd settlement (1 card per adjacent non-desert tile)
    hand: dict[str, int] = {}
    for num, res in board.settlement_dict[placed[1]]['numres']:
        if num != 0:
            hand[res] = hand.get(res, 0) + 1
    if hand:
        hand_str = ", ".join(f"{res}×{cnt}" for res, cnt in sorted(hand.items()))
        print()
        print(f"Starting hand (2nd settlement): {hand_str}")

    # Ports held
    ports_held = []
    for node in placed:
        p = board.settlement_dict[node]['port']
        if p:
            ports_held.append(f"{_PORT_LABEL[p].strip()} (node {node})")
    if ports_held:
        print(f"Port access: {', '.join(ports_held)}")

    print("═" * 44 + "\n")


def main() -> None:
    print("═" * 44)
    print("  Catan Settlement Placement Trainer")
    print("═" * 44)
    print("Generating board...")

    board = CatanBoard()
    placed: list[int] = []

    for pick_num in range(1, 3):
        valid = board.valid_placements(placed)
        pre_recs = recommend(board, placed, top_n=5)

        render_board(board, placed=placed, valid=valid)

        print(f"─── Settlement {pick_num} of 2 ───")
        if pre_recs:
            hints = "  ".join(f"node {n}({s:.1f})" for n, s in pre_recs[:3])
            print(f"Top suggestions: {hints}")

        while True:
            try:
                raw = input(f"\nEnter node number for settlement {pick_num}: ").strip()
                node = int(raw)
                if node in valid:
                    break
                print(f"  Invalid. Valid nodes: {sorted(valid)}")
            except ValueError:
                print("  Please enter a number.")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                sys.exit(0)

        placed.append(node)
        print_placement_feedback(pick_num, node, placed, board, pre_recs)

    print_summary(placed, board)


if __name__ == "__main__":
    main()
