"""Catan Settlement Placement Trainer — Streamlit web app."""
import os
import random
import sys

# Make the catan package importable and app helpers importable.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_REPO_ROOT, "catan_breakdown"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

from catan.board import CatanBoard
from catan.scoring import score_placement, percentile_rank
from catan.recommender import recommend


def _simulate_picks(board: CatanBoard, all_placed: list[int], n_picks: int) -> list[int]:
    """Simulate n_picks AI opponent settlements, each chosen randomly from the top 3 available."""
    picks: list[int] = []
    current = list(all_placed)
    for _ in range(n_picks):
        valid = board.valid_placements(current)
        if not valid:
            break
        scored = sorted(
            valid,
            key=lambda n: score_placement(current + [n], board)["composite_score"],
            reverse=True,
        )
        chosen = random.choice(scored[:min(3, len(scored))])
        picks.append(chosen)
        current.append(chosen)
    return picks

import board_viz
import ui_helpers
from geo import compute_node_positions
from config import BUY_ME_A_COFFEE_URL

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
    ai_placed = st.session_state.get("ai_placements", [])
    all_placed = placed + ai_placed
    cache: dict[int, float] = {}
    for n in board.valid_placements(all_placed):
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
        if "trainer_mode" not in st.session_state:
            st.session_state.trainer_mode = True
        if "num_players" not in st.session_state:
            st.session_state.num_players = 4
        # Randomly assign the user's position in the snake draft
        num_players = st.session_state.num_players
        player_position = random.randint(0, num_players - 1)
        st.session_state.player_position = player_position
        # Simulate picks by players who go before the user
        ai_pre = _simulate_picks(board, [], player_position)
        st.session_state.ai_placements = ai_pre
        _refresh_score_cache()


def _handle_click(node_id: int) -> bool:
    """Process a node click. Returns True if the click was valid and placed."""
    board = st.session_state.board
    placed = st.session_state.placed
    ai_placed = st.session_state.get("ai_placements", [])
    all_placed = placed + ai_placed
    valid = board.valid_placements(all_placed)

    if node_id not in valid:
        return False

    # Capture recommendations before this pick (valid nodes exclude opponent settlements).
    recs = recommend(board, placed, top_n=5, lookahead=False, blocked=ai_placed)
    st.session_state.pre_recs.append(recs)

    placed = placed + [node_id]
    st.session_state.placed = placed

    sc = score_placement(placed, board)
    st.session_state.scores_history.append(sc)

    pct = percentile_rank(placed, board, n_simulations=500)
    st.session_state.percentile_history.append(pct)

    # After the user's first pick, simulate AI picks that happen before the user's second pick.
    if len(placed) == 1:
        num_players = st.session_state.get("num_players", 4)
        player_pos = st.session_state.get("player_position", 0)
        n_ai = 2 * (num_players - 1 - player_pos)
        if n_ai > 0:
            new_ai = _simulate_picks(board, placed + ai_placed, n_ai)
            st.session_state.ai_placements = ai_placed + new_ai

    if len(placed) >= 2:
        st.session_state.phase = "done"

    _refresh_score_cache()
    return True


# ── Sidebar ──────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    board = st.session_state.board
    placed = st.session_state.placed
    phase = st.session_state.phase
    trainer_mode = st.session_state.get("trainer_mode", True)
    ai_placed = st.session_state.get("ai_placements", [])
    num_players = st.session_state.get("num_players", 4)
    player_pos = st.session_state.get("player_position", 0)

    st.sidebar.title("Catan Placement Trainer")

    # Trainer mode toggle
    new_trainer = st.sidebar.checkbox("🎓 Trainer Mode", value=trainer_mode)
    if new_trainer != trainer_mode:
        st.session_state.trainer_mode = new_trainer
        trainer_mode = new_trainer

    # Control buttons
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🔀 New Board", use_container_width=True):
            saved_trainer = st.session_state.get("trainer_mode", True)
            saved_num_players = st.session_state.get("num_players", 4)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.session_state.trainer_mode = saved_trainer
            st.session_state.num_players = saved_num_players
            st.rerun()
    with col2:
        if st.button("↩ Reset Picks", use_container_width=True, disabled=(len(placed) == 0)):
            st.session_state.placed = []
            st.session_state.phase = "placing"
            st.session_state.scores_history = []
            st.session_state.percentile_history = []
            st.session_state.pre_recs = []
            st.session_state.board_ver += 1
            # Re-run pre-game AI picks for the same player position
            ai_pre = _simulate_picks(board, [], player_pos)
            st.session_state.ai_placements = ai_pre
            _refresh_score_cache()
            st.rerun()

    st.sidebar.divider()

    # Game setup (show before first pick so user can change num_players)
    if len(placed) == 0:
        new_num = st.sidebar.selectbox(
            "Players in game",
            options=[2, 3, 4],
            index=[2, 3, 4].index(num_players),
            key="num_players_select",
        )
        if new_num != num_players:
            st.session_state.num_players = new_num
            # Re-randomise position and re-run pre-game picks for new player count
            new_pos = random.randint(0, new_num - 1)
            st.session_state.player_position = new_pos
            ai_pre = _simulate_picks(board, [], new_pos)
            st.session_state.ai_placements = ai_pre
            _refresh_score_cache()
            st.rerun()

    # Always show turn position
    ordinal_pos = ui_helpers.ordinal(player_pos + 1)
    st.sidebar.caption(
        f"You are the **{ordinal_pos} player** of {num_players} "
        f"(pick {player_pos + 1} and {2 * num_players - player_pos} in snake draft)"
    )

    # Show pre-game opponent picks (nodes taken before user's first turn)
    pre_game_picks = ai_placed[:player_pos]
    if pre_game_picks:
        st.sidebar.caption(
            "Before your turn, opponents took: "
            + ", ".join(
                f"node {n} ({board.pip_count(n)} pips)" for n in pre_game_picks
            )
        )

    st.sidebar.divider()

    hiding = trainer_mode and phase == "placing"

    # Placement phase prompt
    if phase == "placing":
        pick_n = len(placed) + 1
        if hiding:
            st.sidebar.info(
                f"**Pick {pick_n} of 2** — click a node on the board.\n\n"
                "Scores are hidden in Trainer Mode. Make your pick, then see how you did!"
            )
        else:
            st.sidebar.info(f"**Pick {pick_n} of 2** — click a green/yellow node on the board")

    # Show inter-pick opponent settlements after user's first pick
    inter_picks = ai_placed[player_pos:]
    if inter_picks and len(placed) >= 1:
        st.sidebar.write(
            "**Opponents took between your picks:** "
            + ", ".join(
                f"node {n} ({board.pip_count(n)} pips)" for n in inter_picks
            )
        )

    # Recommendations: shown immediately in normal mode; only revealed after done in trainer mode
    if not hiding:
        if phase == "placing":
            recs = recommend(board, placed, top_n=5, lookahead=False, blocked=ai_placed)
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

    # Trainer mode reveal: show everything after both picks are done
    if trainer_mode and phase == "done" and len(placed) == 2:
        st.sidebar.subheader("🎯 Scores Revealed!")
        for i, (sc, pct) in enumerate(
            zip(st.session_state.scores_history, st.session_state.percentile_history)
        ):
            st.sidebar.subheader(f"📊 Settlement {i + 1} — Node {placed[i]}")
            df = ui_helpers.format_score_table(sc)
            st.sidebar.dataframe(df, hide_index=True, use_container_width=True)
            st.sidebar.metric("Percentile", f"{ui_helpers.ordinal(round(pct))}")

            if i < len(st.session_state.pre_recs):
                pre = st.session_state.pre_recs[i]
                if pre:
                    top_node, top_score = pre[0]
                    chosen = placed[i]
                    st.sidebar.write("**🤖 Top picks before this selection:**")
                    for rank, (nid, s) in enumerate(pre[:5], 1):
                        pips = board.pip_count(nid)
                        port = board.settlement_dict[nid].get("port")
                        port_str = f" · {ui_helpers.port_label(port)}" if port else ""
                        marker = " ← your pick" if nid == chosen else ""
                        st.sidebar.write(
                            f"**#{rank}** Node {nid} — {s:.1f} ({pips} pips{port_str}){marker}"
                        )
                    if chosen != top_node:
                        gap = top_score - sc["composite_score"]
                        st.sidebar.warning(
                            f"AI top pick was Node {top_node} ({top_score:.1f}) "
                            f"— {gap:.1f} pts difference"
                        )
                    else:
                        st.sidebar.success("✅ You picked the top recommendation!")

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

    if BUY_ME_A_COFFEE_URL:
        st.sidebar.divider()
        st.sidebar.markdown(
            f'<a href="{BUY_ME_A_COFFEE_URL}" target="_blank">'
            '<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png"'
            ' alt="Buy Me A Coffee" style="height:40px;width:auto;"></a>',
            unsafe_allow_html=True,
        )


# ── Main ─────────────────────────────────────────────────────────────────────

_init_state()
_render_sidebar()

st.title("Catan Settlement Trainer")

phase = st.session_state.phase
placed = st.session_state.placed
trainer_mode = st.session_state.get("trainer_mode", True)

if trainer_mode and phase == "placing":
    st.caption(
        "Trainer Mode: all valid nodes are shown in gray — no scores revealed. "
        "Click a node to place your settlement. "
        "Faded nodes are too close to an existing settlement."
    )
else:
    st.caption(
        "Click a coloured node to place your settlement. "
        "Green = high score · Red = low score. "
        "Faded nodes are too close to an existing settlement."
    )

if phase == "done":
    if trainer_mode:
        st.success("Both settlements placed! Scores revealed — check the sidebar to see how you did.")
    else:
        st.success("Both settlements placed! Check the sidebar for your score breakdown.")

fig = board_viz.build_board_figure(
    st.session_state.board,
    placed,
    st.session_state.node_positions,
    st.session_state.node_score_cache,
    trainer_mode=trainer_mode,
    phase=phase,
    ai_placed=st.session_state.get("ai_placements", []),
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
