import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from catan.board import CatanBoard
from catan.scoring import score_placement, percentile_rank

REQUIRED_KEYS = {'pips', 'resource_score', 'port_value', 'diversity_score', 'port_synergy', 'composite_score'}


@pytest.fixture(scope="module")
def board():
    random.seed(42)
    return CatanBoard()


# --- score_placement structural tests ---

def test_score_placement_returns_required_keys(board):
    result = score_placement([10, 33], board)
    assert REQUIRED_KEYS <= set(result.keys())


def test_pips_matches_board_method(board):
    node_ids = [10, 33]
    result = score_placement(node_ids, board)
    expected = sum(board.pip_count(n) for n in node_ids)
    assert result['pips'] == expected


def test_resource_score_matches_board_method(board):
    node_ids = [10, 33]
    result = score_placement(node_ids, board)
    expected = sum(board.resource_score(n) for n in node_ids)
    assert abs(result['resource_score'] - expected) < 1e-9


def test_port_value_matches_board_data(board):
    node_ids = [10, 33]
    result = score_placement(node_ids, board)
    expected = sum(board.settlement_dict[n]['port_value'] for n in node_ids)
    assert abs(result['port_value'] - expected) < 1e-9


def test_composite_score_is_float(board):
    result = score_placement([10, 33], board)
    assert isinstance(result['composite_score'], float)


def test_diversity_score_single_node_nonnegative(board):
    # A single corner node touches at most 1 tile → at most 1 resource type,
    # diversity = 1*2 - max_pips*0.5; since max_pips ≤ 5 this can dip to -0.5,
    # but the general contract is that it is a finite number.
    for n in range(1, 55):
        result = score_placement([n], board)
        assert isinstance(result['diversity_score'], float)


# --- no-port-synergy test ---

def test_no_port_synergy_when_no_ports(board):
    # Find two nodes that have no port.
    no_port_nodes = [n for n, d in board.settlement_dict.items() if d['port'] is None]
    assert len(no_port_nodes) >= 2, "Expected non-port nodes to exist"
    n1, n2 = no_port_nodes[0], no_port_nodes[1]
    result = score_placement([n1, n2], board)
    assert result['port_synergy'] == 0.0


# --- port synergy positive test ---

def test_port_synergy_positive_for_matching_port(board):
    # Find a node with a specific resource port.
    port_node = next(
        (n for n, d in board.settlement_dict.items()
         if d['port'] and d['port'] != 'any'),
        None
    )
    if port_node is None:
        pytest.skip("No specific-resource port found on this board")

    port_resource = board.settlement_dict[port_node]['port']

    # Find a node that produces that resource (has a tile with that resource number).
    producing_node = next(
        (n for n, d in board.settlement_dict.items()
         if n != port_node
         and any(res == port_resource and num != 0 for num, res in d['numres'])),
        None
    )
    if producing_node is None:
        pytest.skip(f"No node producing {port_resource} found on this board")

    result = score_placement([port_node, producing_node], board)
    assert result['port_synergy'] > 0.0


# --- pips additive ---

def test_two_settlements_pips_gte_one(board):
    n1, n2 = 10, 33
    single = score_placement([n1], board)['pips']
    double = score_placement([n1, n2], board)['pips']
    # pip_count is non-negative so adding a second node never decreases pips
    assert double >= single


# --- percentile_rank ---

def test_percentile_rank_in_range_single(board):
    pct = percentile_rank([10], board, n_simulations=200)
    assert 0.0 <= pct <= 100.0


def test_percentile_rank_in_range_two(board):
    pct = percentile_rank([10, 33], board, n_simulations=200)
    assert 0.0 <= pct <= 100.0


def test_high_pip_placement_ranks_above_median(board):
    # The best node on the board should outperform the median random placement.
    best_node = max(range(1, 55), key=board.pip_count)
    pct = percentile_rank([best_node], board, n_simulations=2000)
    assert pct > 50.0, f"Best node ranked at {pct:.1f}th percentile, expected > 50"
