import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from catan.board import CatanBoard
from catan.game_flow import SnakeDraft

# Non-adjacent nodes safe to use for any player count
_SAFE_NODES = [1, 17, 33, 51, 7, 27, 39, 54]


@pytest.fixture(scope="module")
def board():
    random.seed(42)
    return CatanBoard()


def test_snake_order_2_players(board):
    draft = SnakeDraft(2, board)
    assert draft.turn_order == [0, 1, 1, 0]


def test_snake_order_3_players(board):
    draft = SnakeDraft(3, board)
    assert draft.turn_order == [0, 1, 2, 2, 1, 0]


def test_snake_order_4_players(board):
    draft = SnakeDraft(4, board)
    assert draft.turn_order == [0, 1, 2, 3, 3, 2, 1, 0]


def test_turn_order_length(board):
    for n in [2, 3, 4]:
        draft = SnakeDraft(n, board)
        assert len(draft.turn_order) == n * 2


def test_current_player_sequence_matches_turn_order(board):
    for num_players in [2, 3, 4]:
        draft = SnakeDraft(num_players, board)
        expected = list(draft.turn_order)
        observed = []
        for node in _SAFE_NODES[:num_players * 2]:
            observed.append(draft.current_player)
            draft.place(node)
        assert observed == expected, (
            f"{num_players}p: expected {expected}, got {observed}"
        )
