import random

from catan.board import CatanBoard


def score_placement(node_ids: list[int], board: CatanBoard) -> dict:
    """Score a 1- or 2-settlement placement, returning all metrics as a dict.

    Keys: pips, resource_score, port_value, diversity_score, port_synergy,
          composite_score.
    """
    pips = sum(board.pip_count(n) for n in node_ids)
    resource_score = sum(board.resource_score(n) for n in node_ids)
    port_value = sum(board.settlement_dict[n]['port_value'] for n in node_ids)

    # Aggregate pip contribution per resource type across all placements.
    resource_pips: dict[str, int] = {r: 0 for r in ('wood', 'brick', 'sheep', 'wheat', 'ore')}
    for n in node_ids:
        for num, res in board.settlement_dict[n]['numres']:
            if num != 0:
                resource_pips[res] += board.pipdict[num]

    # Diversity: reward covering many distinct resources, penalise concentration.
    n_distinct = sum(1 for v in resource_pips.values() if v > 0)
    max_pips_single = max(resource_pips.values(), default=0)
    diversity_score = n_distinct * 2.0 - max_pips_single * 0.5

    # Port synergy: 2:1 resource ports become more valuable when the placement
    # already generates a lot of that resource.
    port_synergy = 0.0
    for n in node_ids:
        port = board.settlement_dict[n]['port']
        if port and port != 'any' and port in resource_pips:
            port_synergy += resource_pips[port] * 0.3

    composite_score = float(
        pips            * 1.0
        + resource_score  * 0.5
        + port_value      * 2.0
        + diversity_score * 1.0
        + port_synergy    * 1.0
    )

    return {
        'pips': pips,
        'resource_score': resource_score,
        'port_value': port_value,
        'diversity_score': diversity_score,
        'port_synergy': port_synergy,
        'composite_score': composite_score,
    }


def percentile_rank(
    node_ids: list[int],
    board: CatanBoard,
    n_simulations: int = 1000,
) -> float:
    """Return percentile rank (0–100) of the placement vs random legal placements.

    Uses Monte Carlo: sample n_simulations random placements of the same
    number of settlements and compare composite scores.
    """
    user_score = score_placement(node_ids, board)['composite_score']
    n_settle = len(node_ids)
    all_nodes = list(board.settlement_dict.keys())

    scores: list[float] = []
    for _ in range(n_simulations):
        first = random.choice(all_nodes)
        if n_settle == 1:
            sim = [first]
        else:
            rest = board.valid_placements([first])
            if not rest:
                continue
            sim = [first, random.choice(rest)]
        scores.append(score_placement(sim, board)['composite_score'])

    if not scores:
        return 50.0

    return sum(s < user_score for s in scores) / len(scores) * 100.0
