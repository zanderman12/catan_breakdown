import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from catan.board import CatanBoard
from catan.recommender import recommend
from catan.scoring import score_placement


@pytest.fixture(scope="module")
def board():
    random.seed(42)
    return CatanBoard()


# --- Structure ---

def test_recommend_returns_list(board):
    assert isinstance(recommend(board, []), list)


def test_recommend_elements_are_two_tuples(board):
    for item in recommend(board, []):
        assert isinstance(item, tuple) and len(item) == 2


def test_recommend_node_ids_are_int(board):
    for node_id, _ in recommend(board, []):
        assert isinstance(node_id, int)


def test_recommend_scores_are_float(board):
    for _, score in recommend(board, []):
        assert isinstance(score, float)


# --- top_n ---

def test_recommend_default_top_n_is_5(board):
    assert len(recommend(board, [])) == 5


def test_recommend_top_n_respected(board):
    for n in [1, 3, 10]:
        assert len(recommend(board, [], top_n=n)) == n


def test_recommend_top_n_larger_than_candidates_returns_all(board):
    placed = []
    while True:
        legal = board.valid_placements(placed)
        if not legal:
            break
        placed.append(legal[0])
    assert recommend(board, placed, top_n=100) == []


# --- Sort order ---

def test_recommend_sorted_descending(board):
    scores = [s for _, s in recommend(board, [], top_n=10)]
    assert scores == sorted(scores, reverse=True)


def test_recommend_top1_is_argmax(board):
    legal = board.valid_placements([])
    best_node = max(legal, key=lambda n: score_placement([n], board)["composite_score"])
    top_node, _ = recommend(board, [], top_n=1)[0]
    assert top_node == best_node


# --- Node validity ---

def test_recommend_nodes_are_legal(board):
    placed = [10, 33]
    legal = set(board.valid_placements(placed))
    for node_id, _ in recommend(board, placed, top_n=20):
        assert node_id in legal


def test_recommend_excludes_placed_nodes(board):
    placed = [10, 33]
    returned = {node_id for node_id, _ in recommend(board, placed, top_n=20)}
    assert 10 not in returned
    assert 33 not in returned


# --- Score accuracy ---

def test_recommend_greedy_score_matches_score_placement(board):
    placed = [10]
    for node_id, score in recommend(board, placed, top_n=5, lookahead=False):
        expected = score_placement(placed + [node_id], board)["composite_score"]
        assert abs(score - expected) < 1e-9


# --- Lookahead ---

def test_recommend_lookahead_returns_correct_length(board):
    assert len(recommend(board, [], top_n=5, lookahead=True)) == 5


def test_recommend_lookahead_sorted_descending(board):
    scores = [s for _, s in recommend(board, [], top_n=10, lookahead=True)]
    assert scores == sorted(scores, reverse=True)


def test_recommend_lookahead_nodes_are_legal(board):
    placed = [10]
    legal = set(board.valid_placements(placed))
    for node_id, _ in recommend(board, placed, top_n=10, lookahead=True):
        assert node_id in legal


def test_recommend_lookahead_score_is_pair_score(board):
    placed = []
    for node_a, returned_score in recommend(board, placed, top_n=3, lookahead=True):
        placed_with_a = placed + [node_a]
        candidates_b = board.valid_placements(placed_with_a)
        if candidates_b:
            expected = max(
                score_placement(placed_with_a + [b], board)["composite_score"]
                for b in candidates_b
            )
        else:
            expected = score_placement(placed_with_a, board)["composite_score"]
        assert abs(returned_score - expected) < 1e-9


def test_recommend_lookahead_no_crash_on_near_full_board(board):
    placed = []
    while True:
        legal = board.valid_placements(placed)
        if len(legal) <= 3:
            break
        placed.append(legal[0])
    result = recommend(board, placed, top_n=5, lookahead=True)
    assert isinstance(result, list)


# --- Empty board ---

def test_recommend_empty_placed_returns_results(board):
    result = recommend(board, [], top_n=5)
    assert len(result) == 5
    assert all(1 <= node_id <= 54 for node_id, _ in result)
