"""Catan Settlement Placement Trainer — Streamlit web app."""
import os
import sys

# Make the catan package importable and app helpers importable.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, "catan_breakdown"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from catan.board import CatanBoard
from catan.scoring import score_placement, percentile_rank
from catan.recommender import recommend

import board_viz
import ui_helpers
from geo import compute_node_positions

st.set_page_config(
    page_title="Catan Placement Trainer",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── State helpers ────────────────────────────────────────────────────────────

def _refresh_score_cache() -> None:
    """Recompute composite_score for every currently valid node."""
    board = st.session_state.board
    placed = st.session_state.placed
    cache: dict[int, float] = {}
    for n in board.valid_placements(placed):
        cache[n] = score_placement(placed + [n], board)["composite_score"]
    st.session_state.node_score_cache = cache


def _init_state() -> None:
    if "board" not in st.session_state:
        board = CatanBoard()
        st.session_state.board = board
        st.session_state.placed = []
        st.session_state.phase = "placing"
        st.session_state.scores_history = []
        st.session_state.percentile_history = []
        st.session_state.pre_recs = []
        st.session_state.node_positions = compute_node_positions()
        st.session_state.board_ver = 0
        _refresh_score_cache()


def _handle_click(node_id: int) -> bool:
    """Process a node click. Returns True if the click was valid and placed."""
    board = st.session_state.board
    placed = st.session_state.placed
    valid = board.valid_placements(placed)

    if node_id not in valid:
        return False

    # Capture recommendations made before this pick.
    recs = recommend(board, placed, top_n=5, lookahead=False)
    st.session_state.pre_recs.append(recs)

    placed = placed + [node_id]
    st.session_state.placed = placed

    sc = score_placement(placed, board)
    st.session_state.scores_history.append(sc)

    pct = percentile_rank(placed, board, n_simulations=500)
    st.session_state.percentile_history.append(pct)

    if len(placed) >= 2:
        st.session_state.phase = "done"

    _refresh_score_cache()
    return True


# ── Sidebar ──────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    board = st.session_state.board
    placed = st.session_state.placed
    phase = st.session_state.phase

    st.sidebar.title("Catan Placement Trainer")

    # Control buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔀 New Board", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    with col2:
        if st.button("↩ Reset Picks", use_container_width=True, disabled=(len(placed) == 0)):
            st.session_state.placed = []
            st.session_state.phase = "placing"
            st.session_state.scores_history = []
            st.session_state.percentile_history = []
            st.session_state.pre_recs = []
            st.session_state.board_ver += 1
            _refresh_score_cache()
            st.rerun()

    st.sidebar.divider()

    # Placement phase: show pick prompt + recommendations
    if phase == "placing":
        pick_n = len(placed) + 1
        st.sidebar.info(f"**Pick {pick_n} of 2** — click a green/yellow node on the board")

        recs = recommend(board, placed, top_n=5, lookahead=False)
        if recs:
            st.sidebar.subheader("🤖 Top Picks")
            for rank, (nid, score) in enumerate(recs, 1):
                pips = board.pip_count(nid)
                port = board.settlement_dict[nid].get("port")
                port_str = f" · {ui_helpers.port_label(port)}" if port else ""
                st.sidebar.write(f"**#{rank}** Node {nid} — {score:.1f} ({pips} pips{port_str})")

    # Score breakdown after each pick
    for i, (sc, pct) in enumerate(
        zip(st.session_state.scores_history, st.session_state.percentile_history)
    ):
        st.sidebar.subheader(f"📊 Settlement {i + 1}")
        df = ui_helpers.format_score_table(sc)
        st.sidebar.dataframe(df, hide_index=True, use_container_width=True)
        st.sidebar.metric(f"Percentile", f"{ui_helpers.ordinal(round(pct))}")

        if i < len(st.session_state.pre_recs) and i < len(placed):
            pre = st.session_state.pre_recs[i]
            if pre:
                top_node, top_score = pre[0]
                chosen = placed[i]
                if chosen == top_node:
                    st.sidebar.success("✅ You picked the top recommendation!")
                else:
                    gap = top_score - sc["composite_score"]
                    st.sidebar.write(
                        f"AI top pick: Node {top_node} ({top_score:.1f}) "
                        f"— you left {gap:.1f} pts on the table"
                    )

    # Final summary when done
    if phase == "done" and len(placed) == 2:
        st.sidebar.divider()
        st.sidebar.subheader("🎒 Starting Hand")
        hand = ui_helpers.format_starting_hand(placed[1], board)
        st.sidebar.write(f"From node **{placed[1]}**: {hand}")
        ports = [
            board.settlement_dict[n].get("port")
            for n in placed
            if board.settlement_dict[n].get("port")
        ]
        if ports:
            st.sidebar.write("Ports: " + " · ".join(ui_helpers.port_label(p) for p in ports))


# ── Main ─────────────────────────────────────────────────────────────────────

_init_state()
_render_sidebar()

st.title("Catan Settlement Trainer")
st.caption(
    "Click a coloured node to place your settlement. "
    "Green = high score · Red = low score. "
    "Faded nodes are too close to an existing settlement."
)

phase = st.session_state.phase
placed = st.session_state.placed

if phase == "done":
    st.success("Both settlements placed! Check the sidebar for your score breakdown.")

fig = board_viz.build_board_figure(
    st.session_state.board,
    placed,
    st.session_state.node_positions,
    st.session_state.node_score_cache,
)

ver = st.session_state.board_ver
event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key=f"board_{ver}",
)

# Handle click
if event and event.selection and event.selection.points and phase == "placing":
    pt = event.selection.points[0]
    raw = pt.get("customdata")
    # customdata is [[node_id, pips], ...] for valid/placed traces, or int for invalid
    node_id = int(raw[0]) if isinstance(raw, (list, tuple)) else int(raw)

    # Always bump ver so selection clears on next render regardless of validity.
    st.session_state.board_ver += 1

    with st.spinner("Computing score & percentile…"):
        placed_ok = _handle_click(node_id)

    if not placed_ok:
        st.warning(f"Node {node_id} is too close to an existing settlement — pick another.")

    st.rerun()
