import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from catan.board import CatanBoard, ADJACENCY
from catan.game_flow import SnakeDraft

# 8 pairwise non-adjacent nodes (verified against ADJACENCY — no two share a direct edge
# and no node's neighbors include another node in this list)
TEST_NODES = [1, 17, 33, 51, 7, 27, 39, 54]


@pytest.fixture(scope="module")
def board():
    random.seed(42)
    return CatanBoard()


def _draft_to_second_pick(board, target_node, num_players=2):
    """Return a SnakeDraft where target_node is the next (final) valid pick for P0's 2nd placement.

    Uses a 2-player draft ([0,1,1,0]) and fills picks 0-2 with nodes that
    are not adjacent to target_node, leaving target_node available for pick 3.
    """
    excluded = {target_node} | set(ADJACENCY[target_node])
    draft = SnakeDraft(num_players, board)
    for _ in range(num_players * 2 - 1):
        node = next(n for n in draft.valid_placements() if n not in excluded)
        draft.place(node)
    return draft


# ── Group A: Snake order ──────────────────────────────────────────────────────

def test_snake_order_2_players(board):
    draft = SnakeDraft(2, board)
    assert draft.turn_order == [0, 1, 1, 0]
    assert len(draft.turn_order) == 4


def test_snake_order_3_players(board):
    draft = SnakeDraft(3, board)
    assert draft.turn_order == [0, 1, 2, 2, 1, 0]


def test_snake_order_4_players(board):
    draft = SnakeDraft(4, board)
    assert draft.turn_order == [0, 1, 2, 3, 3, 2, 1, 0]


def test_invalid_num_players_raises(board):
    with pytest.raises(ValueError):
        SnakeDraft(1, board)
    with pytest.raises(ValueError):
        SnakeDraft(5, board)


# ── Group B: current_player correctness ──────────────────────────────────────

def test_current_player_sequence_3_players(board):
    draft = SnakeDraft(3, board)
    expected_players = [0, 1, 2, 2, 1, 0]
    seen_players = []
    for node in TEST_NODES[:6]:
        seen_players.append(draft.current_player)
        draft.place(node)
    assert seen_players == expected_players


# ── Group C: valid_placements ─────────────────────────────────────────────────

def test_valid_placements_full_board_before_picks(board):
    draft = SnakeDraft(2, board)
    assert len(draft.valid_placements()) == 54


def test_valid_placements_excludes_all_players_nodes_and_neighbors(board):
    draft = SnakeDraft(2, board)
    draft.place(1)   # P0 — neighbors: 2, 9
    draft.place(17)  # P1 — neighbors: 18, 28
    valid = set(draft.valid_placements())
    for n in {1, 2, 9, 17, 18, 28}:
        assert n not in valid


# ── Group D: place() errors ───────────────────────────────────────────────────

def test_place_occupied_node_raises(board):
    draft = SnakeDraft(2, board)
    draft.place(1)
    draft.place(17)
    with pytest.raises(ValueError):
        draft.place(1)  # already occupied


def test_place_adjacent_node_raises(board):
    draft = SnakeDraft(2, board)
    draft.place(1)  # node 1 neighbors: 2, 9
    with pytest.raises(ValueError):
        draft.place(2)  # violates distance rule


def test_place_when_done_raises(board):
    draft = SnakeDraft(2, board)
    for node in TEST_NODES[:4]:
        draft.place(node)
    assert draft.done
    with pytest.raises(ValueError):
        draft.place(TEST_NODES[4])


# ── Group E: return values ────────────────────────────────────────────────────

def test_place_first_returns_none(board):
    draft = SnakeDraft(2, board)
    assert draft.place(1) is None


def test_place_second_returns_resource_dict(board):
    draft = SnakeDraft(2, board)
    # turn_order = [0, 1, 1, 0]: picks 0 and 1 are first placements
    draft.place(1)   # P0 first → None
    draft.place(17)  # P1 first → None
    result = draft.place(33)  # P1 second → dict
    assert isinstance(result, dict)
    valid_resources = {'wood', 'brick', 'sheep', 'wheat', 'ore'}
    assert all(k in valid_resources for k in result)
    assert all(isinstance(v, int) and v > 0 for v in result.values())


# ── Group F: starting resources ───────────────────────────────────────────────

def test_starting_resources_matches_numres(board):
    target = TEST_NODES[3]  # node 51 — P0's 2nd pick in a 2-player draft
    draft = _draft_to_second_pick(board, target)
    result = draft.place(target)

    expected = {}
    for num, res in board.settlement_dict[target]['numres']:
        if num != 0:
            expected[res] = expected.get(res, 0) + 1
    assert result == expected


def test_starting_resources_desert_excluded(board):
    desert_node = next(
        (node_id for node_id, data in board.settlement_dict.items()
         if any(num == 0 for num, _res in data['numres'])),
        None,
    )
    if desert_node is None:
        pytest.skip("No node touches a desert hex on this board")

    draft = _draft_to_second_pick(board, desert_node)
    assert desert_node in draft.valid_placements(), "desert_node unavailable as final pick"
    result = draft.place(desert_node)

    for num, res in board.settlement_dict[desert_node]['numres']:
        if num == 0:
            assert res not in result


def test_starting_resources_multiple_same_type(board):
    multi_node = next(
        (node_id for node_id, data in board.settlement_dict.items()
         if len([res for num, res in data['numres'] if num != 0]) >
            len({res for num, res in data['numres'] if num != 0})),
        None,
    )
    if multi_node is None:
        pytest.skip("No node touches duplicate resource types on this board")

    draft = _draft_to_second_pick(board, multi_node)
    assert multi_node in draft.valid_placements(), "multi_node unavailable as final pick"
    result = draft.place(multi_node)

    assert any(count >= 2 for count in result.values())


# ── Group G: done flag ────────────────────────────────────────────────────────

def test_not_done_mid_draft(board):
    draft = SnakeDraft(2, board)
    for node in TEST_NODES[:3]:
        draft.place(node)
    assert not draft.done


def test_done_after_all_picks_2_players(board):
    draft = SnakeDraft(2, board)
    for node in TEST_NODES[:4]:
        draft.place(node)
    assert draft.done


def test_done_after_all_picks_4_players(board):
    draft = SnakeDraft(4, board)
    for node in TEST_NODES[:8]:
        draft.place(node)
    assert draft.done


# ── Group H: is_first_placement ──────────────────────────────────────────────

def test_is_first_placement_true_before_any_pick(board):
    draft = SnakeDraft(2, board)
    assert draft.is_first_placement() is True


def test_is_first_placement_false_on_second_turn(board):
    draft = SnakeDraft(2, board)
    # turn_order = [0, 1, 1, 0]: after picks 0 and 1, current_player is P1 again
    draft.place(TEST_NODES[0])  # P0 first
    draft.place(TEST_NODES[1])  # P1 first
    assert draft.current_player == 1
    assert draft.is_first_placement() is False
