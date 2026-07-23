from __future__ import annotations

from catan.board import CatanBoard
from catan.scoring import score_placement


def _greedy_score(node: int, placed: list[int], board: CatanBoard) -> float:
    return score_placement(placed + [node], board)["composite_score"]


def _lookahead_score(node_a: int, placed: list[int], board: CatanBoard) -> float:
    placed_with_a = placed + [node_a]
    candidates_b = board.valid_placements(placed_with_a)
    if not candidates_b:
        return _greedy_score(node_a, placed, board)
    return max(
        score_placement(placed_with_a + [b], board)["composite_score"]
        for b in candidates_b
    )


def recommend(
    board: CatanBoard,
    placed_so_far: list[int],
    top_n: int = 5,
    lookahead: bool = False,
    blocked: list[int] | None = None,
) -> list[tuple[int, float]]:
    """Return top-N recommended settlement nodes with their scores.

    Parameters
    ----------
    board : CatanBoard
    placed_so_far : list[int]
        Node IDs the user has already placed; used as the scoring prefix.
    top_n : int
        Maximum results to return.
    lookahead : bool
        If True, score each candidate by the best achievable pair score
        (this pick + optimal next pick).  If False, score by greedy
        composite_score of placed_so_far + [node].
    blocked : list[int] | None
        Additional node IDs (e.g. opponent settlements) that are off-limits
        but should not be included in the user's score calculation.

    Returns
    -------
    list[tuple[int, float]]
        (node_id, score) pairs sorted descending by score, length <= top_n.
    """
    all_blocked = list(placed_so_far) + (list(blocked) if blocked else [])
    candidates = board.valid_placements(all_blocked)
    if not candidates:
        return []

    if lookahead:
        scorer = lambda node: _lookahead_score(node, placed_so_far, board)
    else:
        scorer = lambda node: _greedy_score(node, placed_so_far, board)

    scored = [(node, scorer(node)) for node in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_n]
