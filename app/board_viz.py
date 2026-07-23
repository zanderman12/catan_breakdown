"""Build the Plotly figure for the Catan board."""
import plotly.graph_objects as go
from geo import tile_polygon_xy, compute_tile_center

RESOURCE_COLORS: dict[str, str] = {
    "wood":   "#2d6a27",
    "brick":  "#9b3030",
    "ore":    "#64748b",
    "sheep":  "#7dc95e",
    "wheat":  "#eab308",
    "desert": "#d4b483",
}

_PORT_LABEL: dict[str, str] = {
    "wood": "WD 2:1", "brick": "BK 2:1", "ore": "OR 2:1",
    "sheep": "SH 2:1", "wheat": "WH 2:1", "any": "3:1",
}


def build_board_figure(
    board,
    placed: list[int],
    node_positions: dict[int, tuple[float, float]],
    node_score_cache: dict[int, float],
    trainer_mode: bool = False,
    phase: str = "placing",
    ai_placed: list[int] | None = None,
) -> go.Figure:
    """Return a Plotly figure with tiles, number tokens, and clickable node markers."""
    fig = go.Figure()

    placed_set = set(placed)
    ai_placed_set = set(ai_placed or [])
    all_placed = list(placed_set | ai_placed_set)
    valid_set = set(board.valid_placements(all_placed))

    # ── Tile polygons + number tokens ────────────────────────────────────────
    for tile_id in board.tile_dict:
        xs, ys = tile_polygon_xy(tile_id, board, node_positions)
        cx, cy = compute_tile_center(tile_id, board, node_positions)

        pts = list(zip(xs, ys))
        path = (
            f"M {pts[0][0]},{pts[0][1]} "
            + " ".join(f"L {x},{y}" for x, y in pts[1:])
            + " Z"
        )
        resource = board.tile_dict[tile_id]["resource"]
        fig.add_shape(
            type="path",
            path=path,
            fillcolor=RESOURCE_COLORS[resource],
            line=dict(color="#111111", width=2),
            layer="below",
        )

        num = board.tile_dict[tile_id]["num"]
        if num > 0:
            pips = board.pipdict[num]
            num_color = "#cc2200" if num in (6, 8) else "#111111"
            fig.add_annotation(
                x=cx, y=cy,
                text=f"<b>{num}</b><br>{'•' * pips}",
                showarrow=False,
                font=dict(size=14, color=num_color),
                bgcolor="rgba(255,255,255,0.85)",
                borderpad=3,
            )

    # ── Port labels (small tag above each port node) ─────────────────────────
    for nid, s in board.settlement_dict.items():
        port = s.get("port")
        if port:
            x, y = node_positions[nid]
            fig.add_annotation(
                x=x, y=y - 14,
                text=f"<span style='font-size:7px'>{_PORT_LABEL.get(port, port)}</span>",
                showarrow=False,
                font=dict(size=7, color="#4b0082"),
                bgcolor="rgba(255,255,255,0.75)",
                borderpad=1,
            )

    # ── Valid nodes ───────────────────────────────────────────────────────────
    if valid_set:
        v_ids = sorted(valid_set)
        scores = [node_score_cache.get(n, 0.0) for n in v_ids]

        hide_scores = trainer_mode and phase == "placing"

        if hide_scores:
            fig.add_trace(go.Scatter(
                x=[node_positions[n][0] for n in v_ids],
                y=[node_positions[n][1] for n in v_ids],
                mode="markers+text",
                marker=dict(
                    color="rgba(150,150,150,0.85)",
                    size=20,
                    symbol="circle",
                    line=dict(color="white", width=1.5),
                ),
                customdata=[[n, board.pip_count(n)] for n in v_ids],
                text=[str(n) for n in v_ids],
                textposition="middle center",
                textfont=dict(size=8, color="black"),
                hovertemplate="<b>Node %{customdata[0]}</b><extra></extra>",
                name="valid",
            ))
        else:
            s_min, s_max = min(scores), max(scores)
            pad = (s_max - s_min) * 0.1 + 0.01
            fig.add_trace(go.Scatter(
                x=[node_positions[n][0] for n in v_ids],
                y=[node_positions[n][1] for n in v_ids],
                mode="markers+text",
                marker=dict(
                    color=scores,
                    colorscale="RdYlGn",
                    cmin=s_min - pad,
                    cmax=s_max + pad,
                    size=20,
                    symbol="circle",
                    line=dict(color="white", width=1.5),
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Score", side="right"),
                        thickness=14,
                        x=1.01,
                        len=0.8,
                    ),
                ),
                customdata=[[n, board.pip_count(n)] for n in v_ids],
                text=[str(n) for n in v_ids],
                textposition="middle center",
                textfont=dict(size=8, color="black"),
                hovertemplate=(
                    "<b>Node %{customdata[0]}</b><br>"
                    "Score: %{marker.color:.1f}<br>"
                    "Pips: %{customdata[1]}"
                    "<extra></extra>"
                ),
                name="valid",
            ))

    # ── Placed nodes (blue stars) ────────────────────────────────────────────
    if placed_set:
        p_ids = list(placed_set)
        fig.add_trace(go.Scatter(
            x=[node_positions[n][0] for n in p_ids],
            y=[node_positions[n][1] for n in p_ids],
            mode="markers+text",
            marker=dict(
                color="#2563eb",
                size=24,
                symbol="star",
                line=dict(color="white", width=2),
            ),
            customdata=[[n, board.pip_count(n)] for n in p_ids],
            text=[str(n) for n in p_ids],
            textposition="top center",
            textfont=dict(size=8, color="white"),
            hovertemplate="<b>Node %{customdata[0]}</b> (your pick)<extra></extra>",
            name="placed",
        ))

    # ── AI-placed nodes (opponent settlements — red X) ────────────────────────
    if ai_placed_set:
        ai_ids = list(ai_placed_set)
        fig.add_trace(go.Scatter(
            x=[node_positions[n][0] for n in ai_ids],
            y=[node_positions[n][1] for n in ai_ids],
            mode="markers+text",
            marker=dict(
                color="#dc2626",
                size=22,
                symbol="x",
                line=dict(color="white", width=2),
            ),
            customdata=[[n, board.pip_count(n)] for n in ai_ids],
            text=[str(n) for n in ai_ids],
            textposition="top center",
            textfont=dict(size=8, color="#dc2626"),
            hovertemplate="<b>Node %{customdata[0]}</b> (opponent)<extra></extra>",
            name="opponent",
        ))

    # ── Invalid nodes (faded, shown for reference) ───────────────────────────
    invalid_ids = [
        n for n in node_positions
        if n not in valid_set and n not in placed_set and n not in ai_placed_set
    ]
    if invalid_ids:
        fig.add_trace(go.Scatter(
            x=[node_positions[n][0] for n in invalid_ids],
            y=[node_positions[n][1] for n in invalid_ids],
            mode="markers",
            marker=dict(
                color="rgba(200,200,200,0.4)",
                size=10,
                symbol="circle",
                line=dict(color="rgba(150,150,150,0.3)", width=1),
            ),
            customdata=invalid_ids,
            hoverinfo="skip",
            name="invalid",
        ))

    # ── Layout ───────────────────────────────────────────────────────────────
    all_x = [p[0] for p in node_positions.values()]
    all_y = [p[1] for p in node_positions.values()]

    fig.update_layout(
        height=520,
        xaxis=dict(visible=False, range=[min(all_x) - 60, max(all_x) + 60]),
        yaxis=dict(
            visible=False,
            range=[max(all_y) + 50, min(all_y) - 50],
            scaleanchor="x",
            scaleratio=1,
        ),
        plot_bgcolor="#1e6fa8",
        paper_bgcolor="white",
        margin=dict(l=10, r=90, t=20, b=10),
        showlegend=False,
        dragmode=False,
    )

    return fig
