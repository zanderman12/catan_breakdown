"""Coordinate conversion: NODE_COORDS (col, row) → pixel (x, y) for Plotly."""
import math
from catan.board import NODE_COORDS

# Scale factors. DX=45 per col unit, DY=95 per row unit gives a visually
# balanced board (widest row ~20 col units, 5 row units tall).
DX: float = 45.0
DY: float = 95.0


def compute_node_positions() -> dict[int, tuple[float, float]]:
    """Return {node_id: (x_pixel, y_pixel)} for all 54 nodes."""
    return {nid: (col * DX, row * DY) for nid, (col, row) in NODE_COORDS.items()}


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
