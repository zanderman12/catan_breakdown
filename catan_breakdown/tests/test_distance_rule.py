import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from catan.board import CatanBoard, ADJACENCY


@pytest.fixture(scope="module")
def board():
    return CatanBoard()


def test_empty_board_all_nodes_valid(board):
    result = board.valid_placements([])
    assert sorted(result) == list(range(1, 55))


def test_placed_node_excluded(board):
    for node in [1, 10, 27, 54]:
        result = board.valid_placements([node])
        assert node not in result


def test_immediate_neighbors_excluded(board):
    for node in [10, 33, 1, 54]:
        result = set(board.valid_placements([node]))
        for neighbor in ADJACENCY[node]:
            assert neighbor not in result, (
                f"Neighbor {neighbor} of placed node {node} should be excluded"
            )


def test_non_adjacent_nodes_remain_valid(board):
    # Node 54 (corner): neighbors are 46 and 53; node 1 is far away
    result = set(board.valid_placements([54]))
    assert 1 in result


def test_two_placements_union_of_exclusions(board):
    # Place at non-adjacent nodes 1 and 54
    result = set(board.valid_placements([1, 54]))
    excluded = {1, 54} | set(ADJACENCY[1]) | set(ADJACENCY[54])
    for node in excluded:
        assert node not in result
    # Every node outside the union should still be valid
    for node in range(1, 55):
        if node not in excluded:
            assert node in result


def test_corner_node_excludes_self_plus_two_neighbors(board):
    # Corner nodes have exactly 2 neighbors (degree 2)
    corner_nodes = [n for n, nb in ADJACENCY.items() if len(nb) == 2]
    assert corner_nodes, "Expected corner nodes with degree 2"
    for node in corner_nodes:
        result = board.valid_placements([node])
        excluded_count = 54 - len(result)
        assert excluded_count == 3, (
            f"Corner node {node} should exclude exactly 3 nodes (self + 2 neighbors), "
            f"got {excluded_count}"
        )


def test_inner_node_excludes_self_plus_three_neighbors(board):
    # Inner nodes have exactly 3 neighbors (degree 3)
    inner_nodes = [n for n, nb in ADJACENCY.items() if len(nb) == 3]
    assert inner_nodes, "Expected inner nodes with degree 3"
    for node in inner_nodes:
        result = board.valid_placements([node])
        excluded_count = 54 - len(result)
        assert excluded_count == 4, (
            f"Inner node {node} should exclude exactly 4 nodes (self + 3 neighbors), "
            f"got {excluded_count}"
        )


def test_returned_nodes_not_adjacent_to_any_placed(board):
    placed = [10, 33]
    result = board.valid_placements(placed)
    placed_set = set(placed)
    for node in result:
        neighbors = set(ADJACENCY[node])
        assert not neighbors & placed_set, (
            f"Returned node {node} is adjacent to a placed node"
        )
