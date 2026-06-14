import sys
import os
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from collections import deque

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from catan.board import CatanBoard

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'placement'
)

SNAKE_ORDER = [0, 1, 2, 3, 3, 2, 1, 0]
N_GAMES = 5000


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    center = (k + z ** 2 / 2) / (n + z ** 2)
    margin = z * math.sqrt(k * (n - k) / n + z ** 2 / 4) / (n + z ** 2)
    return max(0.0, center - margin), center, min(1.0, center + margin)


def node_distance(board: CatanBoard, n1: int, n2: int) -> int:
    if n1 == n2:
        return 0
    visited = {n1}
    q = deque([(n1, 0)])
    while q:
        node, dist = q.popleft()
        for nb in board.adjacency[node]:
            if nb == n2:
                return dist + 1
            if nb not in visited:
                visited.add(nb)
                q.append((nb, dist + 1))
    return 99  # disconnected (shouldn't happen on a connected board)


def reachable_nodes_for_player(board: CatanBoard, player_nodes: list, placed_all: list) -> set:
    """Nodes within 2 road-hops of player's settlements that are still valid placements."""
    one_hop: set = set()
    for n in player_nodes:
        one_hop.update(board.adjacency[n])

    two_hop: set = set()
    for n in one_hop:
        two_hop.update(board.adjacency[n])
    two_hop -= set(player_nodes)

    valid = set(board.valid_placements(placed_all))
    return two_hop & valid


def compute_resource_pips(board: CatanBoard, n1: int, n2: int) -> dict:
    pips = {'wood': 0, 'brick': 0, 'sheep': 0, 'wheat': 0, 'ore': 0}
    for n in (n1, n2):
        for num, res in board.settlement_dict[n]['numres']:
            if num != 0:
                pips[res] += board.pipdict[num]
    return pips


def compute_trading_leverage(board: CatanBoard, n1: int, n2: int, resource_pips: dict) -> float:
    leverage = 0.0
    for n in (n1, n2):
        port = board.settlement_dict[n]['port']
        if port and port != 'any':
            leverage += resource_pips.get(port, 0) * 0.25
        elif port == 'any':
            leverage += board.pip_count(n) * 0.083
    return leverage


def infer_path(resource_pips: dict, diversity: int) -> str:
    city = resource_pips['ore'] + resource_pips['wheat']
    road = resource_pips['wood'] + resource_pips['brick']
    sheep = resource_pips['sheep']
    if city >= 8 and city > road + 2:
        return 'city_builder'
    if road >= 8 and road > city + 2:
        return 'road_runner'
    if diversity >= 4:
        return 'balanced'
    if sheep >= 6:
        return 'sheep_engine'
    return 'other'


def ore_grain_category(has_ore: bool, has_grain: bool) -> str:
    if has_ore and has_grain:
        return 'both'
    if has_ore:
        return 'ore only'
    if has_grain:
        return 'grain only'
    return 'neither'


# ---------------------------------------------------------------------------
# Extended simulation
# ---------------------------------------------------------------------------

def run_simulation_extended(n_games: int) -> pd.DataFrame:
    records = []

    for game_id in range(n_games):
        board = CatanBoard()

        all_scores = {
            n: (board.pip_count(n) + board.resource_score(n) + board.settlement_dict[n]['port_value'])
            for n in board.settlement_dict
        }

        placed_all = []
        player_nodes: dict = {p: [] for p in range(4)}

        for player_idx in SNAKE_ORDER:
            valid = board.valid_placements(placed_all)
            chosen = max(valid, key=lambda n: all_scores[n])
            player_nodes[player_idx].append(chosen)
            placed_all.append(chosen)

        player_totals = []
        for p in range(4):
            n1, n2 = player_nodes[p]

            snps = board.pip_count(n1) + board.pip_count(n2)
            anps = board.resource_score(n1) + board.resource_score(n2)
            pss = (board.settlement_dict[n1]['port_value'] + board.settlement_dict[n2]['port_value'])
            total_score = snps + anps + pss
            player_totals.append(total_score)

            res_pips = compute_resource_pips(board, n1, n2)

            diversity = len([r for r, v in res_pips.items() if v > 0])

            has_ore = res_pips['ore'] > 0
            has_grain = res_pips['wheat'] > 0

            port1 = board.settlement_dict[n1]['port']
            port2 = board.settlement_dict[n2]['port']
            specific = {'wood', 'brick', 'sheep', 'wheat', 'ore'}
            if (port1 in specific) or (port2 in specific):
                port_tier = '2:1'
            elif port1 == 'any' or port2 == 'any':
                port_tier = '3:1'
            else:
                port_tier = 'none'

            nums1 = {num for num, _ in board.settlement_dict[n1]['numres'] if num != 0}
            nums2 = {num for num, _ in board.settlement_dict[n2]['numres'] if num != 0}
            number_overlap_raw = len(nums1 & nums2)
            number_overlap_cat = '2+' if number_overlap_raw >= 2 else str(number_overlap_raw)

            num_6_8 = sum(
                1 for n in (n1, n2)
                for num, _ in board.settlement_dict[n]['numres']
                if num in (6, 8)
            )

            dist = node_distance(board, n1, n2)

            reachable = reachable_nodes_for_player(board, [n1, n2], placed_all)
            reachable_count = len(reachable)

            if reachable:
                best_reach_anps = max(board.resource_score(n) for n in reachable)
                current_resources = {r for r, v in res_pips.items() if v > 0}
                new_res = set()
                for n in reachable:
                    for num, res in board.settlement_dict[n]['numres']:
                        if num != 0 and res not in current_resources:
                            new_res.add(res)
                reachable_new_res = len(new_res)
            else:
                best_reach_anps = 0.0
                reachable_new_res = 0

            trading_leverage = compute_trading_leverage(board, n1, n2, res_pips)
            path = infer_path(res_pips, diversity)
            og_cat = ore_grain_category(has_ore, has_grain)
            both_10_plus = int(board.pip_count(n1) >= 10 and board.pip_count(n2) >= 10)

            records.append({
                'game_id': game_id,
                'turn_order': p + 1,
                'SNPS': snps,
                'ANPS': anps,
                'PSS': pss,
                'total_score': total_score,
                'resource_diversity': diversity,
                'has_ore': int(has_ore),
                'has_grain': int(has_grain),
                'ore_grain_cat': og_cat,
                'port1': port1,
                'port2': port2,
                'port_tier': port_tier,
                'number_overlap_raw': number_overlap_raw,
                'number_overlap': number_overlap_cat,
                'num_6_8_tiles': num_6_8,
                'settlement_distance': dist,
                'reachable_node_count': reachable_count,
                'best_reachable_anps': best_reach_anps,
                'reachable_new_resources': reachable_new_res,
                'ore_pips': res_pips['ore'],
                'wheat_pips': res_pips['wheat'],
                'sheep_pips': res_pips['sheep'],
                'wood_pips': res_pips['wood'],
                'brick_pips': res_pips['brick'],
                'snps_1': board.pip_count(n1),
                'snps_2': board.pip_count(n2),
                'both_10_plus': both_10_plus,
                'trading_leverage': trading_leverage,
                'inferred_path': path,
            })

        max_score = max(player_totals)
        for i, rec in enumerate(records[-4:]):
            rec['win'] = 1 if player_totals[i] == max_score else 0

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Chart utilities
# ---------------------------------------------------------------------------

def _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts, color='steelblue'):
    x = range(len(labels))
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=5, edgecolor='black', color=color, alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        if cnt > 0:
            top = bar.get_height() + (max(hi_errs) * 0.15 if hi_errs else 0.01)
            ax.text(xi, top, f'n={cnt}', ha='center', va='bottom', fontsize=7)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
    ax.set_ylabel('Win Rate')
    ax.legend(fontsize=8)


def _winrate_from_groups(groups):
    """Given dict of {label: sub-dataframe}, return parallel lists for bar chart."""
    labels, win_rates, lo_errs, hi_errs, counts = [], [], [], [], []
    for label, grp in groups.items():
        k = int(grp['win'].sum())
        n = len(grp)
        lo, center, hi = wilson_ci(k, n)
        labels.append(label)
        win_rates.append(center)
        lo_errs.append(center - lo)
        hi_errs.append(hi - center)
        counts.append(n)
    return labels, win_rates, lo_errs, hi_errs, counts


# ---------------------------------------------------------------------------
# Individual chart functions
# ---------------------------------------------------------------------------

def chart7_winrate_by_diversity(df: pd.DataFrame) -> None:
    groups = {}
    for val in sorted(df['resource_diversity'].unique()):
        groups[str(val)] = df[df['resource_diversity'] == val]

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts)
    ax.set_xlabel('Resource Diversity (unique resource types, 0–5)')
    ax.set_title('Win Rate by Resource Diversity\n(Wilson 95% CI)')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'winrate_by_diversity.png'), dpi=150)
    plt.close(fig)
    print('  saved winrate_by_diversity.png')


def chart8_ore_grain_access(df: pd.DataFrame) -> None:
    order = ['both', 'ore only', 'grain only', 'neither']
    groups = {cat: df[df['ore_grain_cat'] == cat] for cat in order}

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9E9E9E']
    x = range(len(labels))
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=5, edgecolor='black', color=colors, alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        ax.text(xi, bar.get_height() + max(hi_errs) * 0.15,
                f'n={cnt}', ha='center', va='bottom', fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_xlabel('Ore / Grain (Wheat) Access')
    ax.set_ylabel('Win Rate')
    ax.set_title('Win Rate by Ore & Grain Access\n(Wilson 95% CI)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'ore_grain_access.png'), dpi=150)
    plt.close(fig)
    print('  saved ore_grain_access.png')


def chart9_port_access_by_type(df: pd.DataFrame) -> None:
    port_labels = ['ore', 'wheat', 'sheep', 'wood', 'brick', 'any', 'none']
    display = ['ore 2:1', 'wheat 2:1', 'sheep 2:1', 'wood 2:1', 'brick 2:1', '3:1 any', 'no port']

    win_rates, lo_errs, hi_errs, counts = [], [], [], []
    for pt in port_labels:
        if pt == 'none':
            mask = (df['port1'].isna() | df['port1'].isnull()) & (df['port2'].isna() | df['port2'].isnull())
            # More robust: no port at all
            mask = df.apply(lambda r: r['port1'] is None and r['port2'] is None, axis=1)
        else:
            mask = (df['port1'] == pt) | (df['port2'] == pt)
        grp = df[mask]
        k = int(grp['win'].sum())
        n = len(grp)
        lo, center, hi = wilson_ci(k, n)
        win_rates.append(center)
        lo_errs.append(center - lo)
        hi_errs.append(hi - center)
        counts.append(n)

    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    x = range(len(display))
    colors = ['#795548', '#FF9800', '#8BC34A', '#4CAF50', '#F44336', '#9C27B0', '#9E9E9E']
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=5, edgecolor='black', color=colors, alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        ax.text(xi, bar.get_height() + max(hi_errs) * 0.15,
                f'n={cnt}', ha='center', va='bottom', fontsize=7)
    ax.set_xticks(list(x))
    ax.set_xticklabels(display, rotation=20, ha='right', fontsize=9)
    ax.set_xlabel('Port Type Held by Player')
    ax.set_ylabel('Win Rate')
    ax.set_title('Win Rate by Port Type Access\n(players may appear in multiple bars; Wilson 95% CI)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'port_access_by_type.png'), dpi=150)
    plt.close(fig)
    print('  saved port_access_by_type.png')


def _binned_winrate_chart(df, col, filename, title, xlabel, n_bins=5):
    df2 = df.copy()
    df2['_bin'] = pd.cut(df2[col], bins=n_bins)
    groups = {}
    for name, grp in df2.groupby('_bin', observed=False):
        groups[str(name)] = grp

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts)
    ax.set_xlabel(xlabel)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, filename), dpi=150)
    plt.close(fig)
    print(f'  saved {filename}')


def chart10_expansion_options(df: pd.DataFrame) -> None:
    _binned_winrate_chart(
        df, 'reachable_node_count',
        'expansion_options_vs_winrate.png',
        'Win Rate by Reachable Node Count (Expansion Options)\n(5 equal-width bins, Wilson 95% CI)',
        'Reachable Node Count (valid settlements within 2 road-hops)',
    )


def chart11_best_reachable_score(df: pd.DataFrame) -> None:
    _binned_winrate_chart(
        df, 'best_reachable_anps',
        'best_reachable_score_vs_winrate.png',
        'Win Rate by Best Reachable ANPS (Expansion Quality)\n(5 equal-width bins, Wilson 95% CI)',
        'Best Reachable ANPS (resource score of best nearby expansion spot)',
    )


def chart12_reachable_new_resources(df: pd.DataFrame) -> None:
    groups = {}
    for val in sorted(df['reachable_new_resources'].unique()):
        groups[str(val)] = df[df['reachable_new_resources'] == val]

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts)
    ax.set_xlabel('New Resource Types Reachable via Expansion (count)')
    ax.set_title('Win Rate by Reachable New Resources\n(Wilson 95% CI)')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'reachable_new_resources_vs_winrate.png'), dpi=150)
    plt.close(fig)
    print('  saved reachable_new_resources_vs_winrate.png')


def chart13_number_overlap(df: pd.DataFrame) -> None:
    groups = {}
    for val in ['0', '1', '2+']:
        groups[val] = df[df['number_overlap'] == val]

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts)
    ax.set_xlabel('Number of Shared Roll Numbers Between Settlements')
    ax.set_title('Win Rate by Roll Number Overlap Between Settlements\n(Wilson 95% CI)')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'number_overlap_vs_winrate.png'), dpi=150)
    plt.close(fig)
    print('  saved number_overlap_vs_winrate.png')


def chart14_robber_exposure(df: pd.DataFrame) -> None:
    groups = {}
    for val in sorted(df['num_6_8_tiles'].unique()):
        groups[str(val)] = df[df['num_6_8_tiles'] == val]

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
    _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts, color='#E57373')
    ax.set_xlabel('Number of 6 or 8 Tiles Touched by Settlements')
    ax.set_title('Win Rate by Robber Exposure (6 & 8 Tiles)\n(Wilson 95% CI)')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'robber_exposure_vs_winrate.png'), dpi=150)
    plt.close(fig)
    print('  saved robber_exposure_vs_winrate.png')


def chart15_settlement_distance(df: pd.DataFrame) -> None:
    groups = {}
    for val in sorted(df['settlement_distance'].unique()):
        groups[str(val)] = df[df['settlement_distance'] == val]

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    _bar_winrate(ax, labels, win_rates, lo_errs, hi_errs, counts, color='#7986CB')
    ax.set_xlabel('Graph Distance Between Settlements (hops)')
    ax.set_title('Win Rate by Settlement Distance\n(Wilson 95% CI)')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'settlement_distance_vs_winrate.png'), dpi=150)
    plt.close(fig)
    print('  saved settlement_distance_vs_winrate.png')


def chart16_ore_wheat_sheep_triangle(df: pd.DataFrame) -> None:
    """Ternary scatter: ore/wheat/sheep pip proportions colored by win rate."""
    ore = df['ore_pips'].values.astype(float)
    wheat = df['wheat_pips'].values.astype(float)
    sheep = df['sheep_pips'].values.astype(float)
    wins = df['win'].values

    total = ore + wheat + sheep
    # Where total == 0, place at centroid
    with np.errstate(invalid='ignore', divide='ignore'):
        a = np.where(total > 0, ore / total, 1 / 3)
        b = np.where(total > 0, wheat / total, 1 / 3)
        c = np.where(total > 0, sheep / total, 1 / 3)

    # Barycentric → cartesian (ore=left, wheat=right, sheep=top)
    tx = 0.5 * (2 * b + c)
    ty = (math.sqrt(3) / 2) * c

    # Bin into a 2D grid and compute local win rate
    n_bins = 20
    x_edges = np.linspace(0, 1, n_bins + 1)
    y_edges = np.linspace(0, math.sqrt(3) / 2 + 0.01, n_bins + 1)
    xi = np.clip(np.digitize(tx, x_edges) - 1, 0, n_bins - 1)
    yi = np.clip(np.digitize(ty, y_edges) - 1, 0, n_bins - 1)

    bin_wr = np.full((n_bins, n_bins), np.nan)
    for bx in range(n_bins):
        for by in range(n_bins):
            mask = (xi == bx) & (yi == by)
            if mask.sum() >= 5:
                bin_wr[bx, by] = wins[mask].mean()

    point_wr = np.array([
        bin_wr[xi[i], yi[i]] if not np.isnan(bin_wr[xi[i], yi[i]]) else np.nan
        for i in range(len(tx))
    ])

    fig, ax = plt.subplots(figsize=(9, 8), dpi=150)

    # Draw triangle boundary
    tri_x = [0.0, 1.0, 0.5, 0.0]
    tri_y = [0.0, 0.0, math.sqrt(3) / 2, 0.0]
    ax.plot(tri_x, tri_y, 'k-', linewidth=1.5)

    # Scatter colored by win rate (only where we have data)
    valid_mask = ~np.isnan(point_wr)
    sc = ax.scatter(tx[valid_mask], ty[valid_mask],
                    c=point_wr[valid_mask], cmap='RdYlGn',
                    vmin=0.0, vmax=0.5, alpha=0.4, s=6, edgecolors='none')
    # Grey points with no bin data
    ax.scatter(tx[~valid_mask], ty[~valid_mask],
               c='lightgrey', alpha=0.15, s=4, edgecolors='none')

    cbar = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('Local Win Rate', fontsize=10)

    # Corner labels
    offset = 0.04
    ax.text(-offset, -offset, 'Ore', ha='center', va='top', fontsize=12, fontweight='bold')
    ax.text(1 + offset, -offset, 'Wheat', ha='center', va='top', fontsize=12, fontweight='bold')
    ax.text(0.5, math.sqrt(3) / 2 + offset, 'Sheep', ha='center', va='bottom', fontsize=12, fontweight='bold')

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, math.sqrt(3) / 2 + 0.15)
    ax.axis('off')
    ax.set_title('Ore / Wheat / Sheep Pip Access — Ternary Plot\n(colored by local win rate)', fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'ore_wheat_sheep_triangle.png'), dpi=150)
    plt.close(fig)
    print('  saved ore_wheat_sheep_triangle.png')


def chart17_first_vs_second_settlement(df: pd.DataFrame) -> None:
    """4 bars: mean SNPS of 1st/2nd settlement for winners vs losers."""
    winners = df[df['win'] == 1]
    losers = df[df['win'] == 0]

    groups = {
        'Winners\n1st Settlement': winners['snps_1'],
        'Winners\n2nd Settlement': winners['snps_2'],
        'Losers\n1st Settlement': losers['snps_1'],
        'Losers\n2nd Settlement': losers['snps_2'],
    }

    labels = list(groups.keys())
    means = [g.mean() for g in groups.values()]
    sems = [stats.sem(g) for g in groups.values()]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    x = range(len(labels))
    colors = ['#4CAF50', '#81C784', '#F44336', '#E57373']
    bars = ax.bar(x, means, yerr=sems, capsize=6, edgecolor='black', color=colors, alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel('Mean SNPS (pip count)')
    ax.set_title('1st vs 2nd Settlement Pip Score: Winners vs Losers\n(error bars = ±1 SEM)')
    for xi, (bar, mean) in enumerate(zip(bars, means)):
        ax.text(xi, bar.get_height() + max(sems) * 0.15,
                f'{mean:.1f}', ha='center', va='bottom', fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'first_vs_second_settlement.png'), dpi=150)
    plt.close(fig)
    print('  saved first_vs_second_settlement.png')


def chart18_ten_pip_minimum(df: pd.DataFrame) -> None:
    groups = {
        'Both ≥10 pips': df[df['both_10_plus'] == 1],
        'Not both ≥10 pips': df[df['both_10_plus'] == 0],
    }
    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    colors = ['#4CAF50', '#9E9E9E']
    x = range(len(labels))
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=6, edgecolor='black', color=colors, alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        ax.text(xi, bar.get_height() + max(hi_errs) * 0.15,
                f'n={cnt}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Win Rate')
    ax.set_title('"10-Pip Minimum Rule": Win Rate When Both Settlements Have ≥10 Pips\n(Wilson 95% CI)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'ten_pip_minimum_rule.png'), dpi=150)
    plt.close(fig)
    print('  saved ten_pip_minimum_rule.png')


def chart19_port_quality_tiers(df: pd.DataFrame) -> None:
    order = ['none', '3:1', '2:1']
    labels = ['No Port', '3:1 (Any)', '2:1 (Specific)']
    groups = {lbl: df[df['port_tier'] == tier] for lbl, tier in zip(labels, order)}

    labels_out, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    colors = ['#9E9E9E', '#9C27B0', '#2196F3']
    x = range(len(labels_out))
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=6, edgecolor='black', color=colors, alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        ax.text(xi, bar.get_height() + max(hi_errs) * 0.15,
                f'n={cnt}', ha='center', va='bottom', fontsize=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels_out, fontsize=11)
    ax.set_ylabel('Win Rate')
    ax.set_title('Win Rate by Port Quality Tier\n(Wilson 95% CI)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'port_quality_tiers.png'), dpi=150)
    plt.close(fig)
    print('  saved port_quality_tiers.png')


def chart20_inferred_path(df: pd.DataFrame) -> None:
    order = ['city_builder', 'road_runner', 'balanced', 'sheep_engine', 'other']
    display = ['City Builder\n(ore+wheat)', 'Road Runner\n(wood+brick)',
               'Balanced\n(4+ resources)', 'Sheep Engine\n(sheep≥6)', 'Other']
    groups = {disp: df[df['inferred_path'] == cat] for disp, cat in zip(display, order)}

    labels, win_rates, lo_errs, hi_errs, counts = _winrate_from_groups(groups)

    fig, ax = plt.subplots(figsize=(11, 5), dpi=150)
    colors = ['#FF9800', '#4CAF50', '#2196F3', '#8BC34A', '#9E9E9E']
    x = range(len(labels))
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=5, edgecolor='black', color=colors, alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        ax.text(xi, bar.get_height() + max(hi_errs) * 0.15,
                f'n={cnt}', ha='center', va='bottom', fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel('Win Rate')
    ax.set_title('Win Rate by Inferred Settlement Strategy\n(Wilson 95% CI)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'inferred_path_vs_winrate.png'), dpi=150)
    plt.close(fig)
    print('  saved inferred_path_vs_winrate.png')


def chart21_trading_leverage(df: pd.DataFrame) -> None:
    _binned_winrate_chart(
        df, 'trading_leverage',
        'trading_leverage_vs_winrate.png',
        'Win Rate by Trading Leverage Score\n(5 equal-width bins, Wilson 95% CI)',
        'Trading Leverage (port efficiency gain over 4:1 baseline)',
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f'Running {N_GAMES} extended simulations...')
    df = run_simulation_extended(N_GAMES)
    print(f'Simulation complete. {len(df)} player records.')

    print('\nGenerating charts 7–21...')
    chart7_winrate_by_diversity(df)
    chart8_ore_grain_access(df)
    chart9_port_access_by_type(df)
    chart10_expansion_options(df)
    chart11_best_reachable_score(df)
    chart12_reachable_new_resources(df)
    chart13_number_overlap(df)
    chart14_robber_exposure(df)
    chart15_settlement_distance(df)
    chart16_ore_wheat_sheep_triangle(df)
    chart17_first_vs_second_settlement(df)
    chart18_ten_pip_minimum(df)
    chart19_port_quality_tiers(df)
    chart20_inferred_path(df)
    chart21_trading_leverage(df)

    print(f'\nAll 15 charts saved to {os.path.abspath(RESULTS_DIR)}')
