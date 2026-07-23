"""Coordinate conversion: NODE_COORDS (x, y) → pixel (px, py) for Plotly."""
import math
from catan.board import NODE_COORDS

# Pixels per coordinate unit.  NODE_COORDS uses y-up convention; Plotly's
# board_viz uses an inverted y-axis (range=[max,min]), so py = -y * SCALE.
SCALE: float = 80.0


def compute_node_positions() -> dict[int, tuple[float, float]]:
    """Return {node_id: (px, py)} for all 54 nodes in Plotly pixel space."""
    return {nid: (x * SCALE, -y * SCALE) for nid, (x, y) in NODE_COORDS.items()}


def compute_tile_center(
    tile_id: int,
    board,
    node_pos: dict[int, tuple[float, float]],
) -> tuple[float, float]:
    """Return (cx, cy) pixel centre of a tile (average of its 6 node positions)."""
    nodes = [n for n, s in board.settlement_dict.items() if tile_id in s["tiles"]]
    cx = sum(node_pos[n][0] for n in nodes) / len(nodes)
    cy = sum(node_pos[n][1] for n in nodes) / len(nodes)
    return cx, cy


def tile_polygon_xy(
    tile_id: int,
    board,
    node_pos: dict[int, tuple[float, float]],
) -> tuple[list[float], list[float]]:
    """Return (xs, ys) of the tile polygon, nodes sorted by angle from centre."""
    nodes = [n for n, s in board.settlement_dict.items() if tile_id in s["tiles"]]
    cx, cy = compute_tile_center(tile_id, board, node_pos)
    nodes.sort(key=lambda n: math.atan2(node_pos[n][1] - cy, node_pos[n][0] - cx))
    return [node_pos[n][0] for n in nodes], [node_pos[n][1] for n in nodes]
