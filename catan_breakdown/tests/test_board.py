import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from catan.board import CatanBoard, ADJACENCY, NODE_COORDS


@pytest.fixture(scope="module")
def board():
    return CatanBoard()


def test_tile_counts(board):
    resources = [t['resource'] for t in board.tile_dict.values()]
    assert resources.count('sheep') == 4
    assert resources.count('wood') == 4
    assert resources.count('wheat') == 4
    assert resources.count('brick') == 3
    assert resources.count('ore') == 3
    assert resources.count('desert') == 1
    assert len(resources) == 19


def test_desert_has_num_zero(board):
    desert_tile = next(t for t in board.tile_dict.values() if t['resource'] == 'desert')
    assert desert_tile['num'] == 0


def test_pipdict_values(board):
    assert board.pipdict[6] == 5
    assert board.pipdict[8] == 5
    assert board.pipdict[2] == 1
    assert board.pipdict[12] == 1
    assert board.pipdict[0] == 0


def test_adjacency_symmetry():
    for node, neighbors in ADJACENCY.items():
        for nb in neighbors:
            assert node in ADJACENCY[nb], f"Node {node} in ADJACENCY[{nb}] expected but missing"


def test_adjacency_degree():
    for node, neighbors in ADJACENCY.items():
        assert 2 <= len(neighbors) <= 3, f"Node {node} has {len(neighbors)} neighbors (expected 2 or 3)"


def test_adjacency_covers_all_nodes():
    assert set(ADJACENCY.keys()) == set(range(1, 55))


def test_node_coords_covers_all_nodes():
    assert set(NODE_COORDS.keys()) == set(range(1, 55))


def test_valid_placements_empty_board(board):
    result = board.valid_placements([])
    assert sorted(result) == list(range(1, 55))


def test_valid_placements_excludes_placed_and_neighbors(board):
    # Node 10 has neighbors [9, 11, 20]
    result = board.valid_placements([10])
    excluded = {9, 10, 11, 20}
    for node in excluded:
        assert node not in result
    assert len(result) == 54 - len(excluded)


def test_valid_placements_two_placements(board):
    # Place at 10 (neighbors: 9,11,20) and 33 (neighbors: 32,34,43)
    result = board.valid_placements([10, 33])
    excluded = {9, 10, 11, 20, 32, 33, 34, 43}
    for node in excluded:
        assert node not in result


def test_settlement_dict_completeness(board):
    assert set(board.settlement_dict.keys()) == set(range(1, 55))
    required_keys = {'tiles', 'port', 'resources', 'numres', 'port_value'}
    for node, data in board.settlement_dict.items():
        assert required_keys <= set(data.keys()), f"Node {node} missing keys"


def test_pip_count_returns_nonnegative(board):
    for node in range(1, 55):
        assert board.pip_count(node) >= 0


def test_resource_score_returns_float(board):
    for node in range(1, 55):
        score = board.resource_score(node)
        assert isinstance(score, float)
        # Score can be negative when a resource is heavily over-supplied on the board
        # (regression formula: value = base - coeff * availability can go negative)
