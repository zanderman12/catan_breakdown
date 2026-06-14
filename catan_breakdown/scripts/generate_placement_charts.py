import sys
import os
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Allow importing the 'catan' package from the catan_breakdown/ directory
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from catan.board import CatanBoard

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'results', 'placement'
)

# Snake draft order (0-indexed): P0 picks 1st and 8th, P3 picks 4th and 5th
SNAKE_ORDER = [0, 1, 2, 3, 3, 2, 1, 0]

N_GAMES = 5000


def resource_diversity(board: CatanBoard, node1: int, node2: int) -> int:
    """Count unique resource types (excluding desert) across both settlements."""
    resources = set()
    for node in (node1, node2):
        for num, res in board.settlement_dict[node]['numres']:
            if num != 0:
                resources.add(res)
    return len(resources)


def run_simulation(n_games: int) -> pd.DataFrame:
    records = []

    for game_id in range(n_games):
        board = CatanBoard()

        # Pre-score all 54 nodes once per board (avoids repeated dict lookups)
        all_scores = {
            n: (board.pip_count(n)
                + board.resource_score(n)
                + board.settlement_dict[n]['port_value'])
            for n in board.settlement_dict
        }

        placed_all = []
        player_nodes = {p: [] for p in range(4)}

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
            pss = (board.settlement_dict[n1]['port_value']
                   + board.settlement_dict[n2]['port_value'])
            player_totals.append(snps + anps + pss)
            records.append({
                'game_id': game_id,
                'turn_order': p + 1,
                'SNPS': snps,
                'ANPS': anps,
                'PSS': pss,
                'resource_diversity': resource_diversity(board, n1, n2),
                'total_score': snps + anps + pss,
            })

        max_score = max(player_totals)
        for i, rec in enumerate(records[-4:]):
            rec['win'] = 1 if player_totals[i] == max_score else 0

    return pd.DataFrame(records)


def plot_scoring_comparison(df: pd.DataFrame) -> None:
    """Chart 1: Pearson r between SNPS/ANPS/PSS and win, with 95% CI."""
    n = len(df)
    metrics = ['SNPS', 'ANPS', 'PSS']
    labels = ['SNPS\n(pip count)', 'ANPS\n(resource score)', 'PSS\n(port synergy)']
    colors = ['#2196F3', '#4CAF50', '#FF9800']

    rs, xerr_low, xerr_high = [], [], []
    for m in metrics:
        r, _ = stats.pearsonr(df[m], df['win'])
        z = math.atanh(r)
        se = 1.0 / math.sqrt(n - 3)
        r_low = math.tanh(z - 1.96 * se)
        r_high = math.tanh(z + 1.96 * se)
        rs.append(r)
        xerr_low.append(r - r_low)
        xerr_high.append(r_high - r)

    fig, ax = plt.subplots(figsize=(9, 4), dpi=150)
    ax.barh(labels, rs, xerr=[xerr_low, xerr_high],
            color=colors, edgecolor='black', capsize=6, height=0.5)
    ax.axvline(0, color='black', linewidth=0.9, linestyle='--')
    ax.set_xlabel('Pearson r with Win (binary)')
    ax.set_title('Scoring System Comparison: Correlation with Win Rate\n(error bars = 95% CI via Fisher Z transform)')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'scoring_comparison.png'), dpi=150)
    plt.close(fig)
    print('  saved scoring_comparison.png')


def wilson_ci(k: int, n: int, z: float = 1.96):
    if n == 0:
        return 0.0, 0.0, 0.0
    center = (k + z ** 2 / 2) / (n + z ** 2)
    margin = z * math.sqrt(k * (n - k) / n + z ** 2 / 4) / (n + z ** 2)
    return max(0.0, center - margin), center, min(1.0, center + margin)


def plot_winrate_by_metric(df: pd.DataFrame, metric: str, filename: str, n_bins: int = 6) -> None:
    """Charts 2-4: Win rate per equal-width bucket of a scoring metric."""
    df = df.copy()
    df['_bin'] = pd.cut(df[metric], bins=n_bins)

    bin_labels, win_rates, lo_errs, hi_errs, counts = [], [], [], [], []
    for name, grp in df.groupby('_bin', observed=False):
        k = int(grp['win'].sum())
        n = len(grp)
        lo, center, hi = wilson_ci(k, n)
        bin_labels.append(str(name))
        win_rates.append(center)
        lo_errs.append(center - lo)
        hi_errs.append(hi - center)
        counts.append(n)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    x = range(len(bin_labels))
    bars = ax.bar(x, win_rates, yerr=[lo_errs, hi_errs],
                  capsize=5, edgecolor='black', color='steelblue', alpha=0.85)
    ax.axhline(0.25, color='red', linestyle='--', linewidth=1.2, label='Expected (25%)')

    # Annotate bar tops with sample count
    for xi, (bar, cnt) in enumerate(zip(bars, counts)):
        if cnt > 0:
            ax.text(xi, bar.get_height() + max(hi_errs) * 0.15,
                    f'n={cnt}', ha='center', va='bottom', fontsize=8)

    ax.set_xticks(list(x))
    ax.set_xticklabels(bin_labels, rotation=30, ha='right', fontsize=8)
    ax.set_xlabel(metric)
    ax.set_ylabel('Win Rate')
    ax.set_title(f'Win Rate by {metric} Bucket\n(6 equal-width bins, Wilson 95% CI)')
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, filename), dpi=150)
    plt.close(fig)
    print(f'  saved {filename}')


def plot_turn_order_scores(df: pd.DataFrame) -> None:
    """Chart 5: Side-by-side box plots of SNPS/ANPS/PSS by turn order."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), dpi=150)
    metrics = ['SNPS', 'ANPS', 'PSS']
    for ax, metric in zip(axes, metrics):
        sns.boxplot(data=df, x='turn_order', y=metric, ax=ax,
                    order=[1, 2, 3, 4], hue='turn_order',
                    palette='Set2', legend=False)
        ax.set_xlabel('Turn Order (1 = first pick)', fontsize=10)
        ax.set_ylabel(metric, fontsize=10)
        ax.set_title(f'{metric} by Turn Order')
    fig.suptitle('Score Distributions by Snake Draft Turn Order', fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'turn_order_vs_scores.png'),
                dpi=150, bbox_inches='tight')
    plt.close(fig)
    print('  saved turn_order_vs_scores.png')


def plot_score_frontier(df: pd.DataFrame, n_bins: int = 15) -> None:
    """Chart 6: ANPS vs resource_diversity scatter, colored by local 2D-bin win rate."""
    anps = df['ANPS'].values
    rdiv = df['resource_diversity'].values
    wins = df['win'].values

    anps_edges = np.linspace(anps.min(), anps.max(), n_bins + 1)
    rdiv_edges = np.linspace(rdiv.min(), rdiv.max(), n_bins + 1)

    ai = np.clip(np.digitize(anps, anps_edges) - 1, 0, n_bins - 1)
    ri = np.clip(np.digitize(rdiv, rdiv_edges) - 1, 0, n_bins - 1)

    bin_wr = np.full((n_bins, n_bins), np.nan)
    for a in range(n_bins):
        for r in range(n_bins):
            mask = (ai == a) & (ri == r)
            if mask.sum() > 0:
                bin_wr[a, r] = wins[mask].mean()

    point_wr = bin_wr[ai, ri]

    fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
    sc = ax.scatter(anps, rdiv, c=point_wr, cmap='RdYlGn',
                    vmin=0.0, vmax=0.5, alpha=0.35, s=8, edgecolors='none')
    cbar = fig.colorbar(sc, ax=ax)
    cbar.set_label('Local Win Rate (2D bin)', fontsize=10)
    ax.set_xlabel('ANPS (Adjusted Resource Score)', fontsize=11)
    ax.set_ylabel('Resource Diversity (unique resources, both settlements)', fontsize=11)
    ax.set_title('Score Frontier: ANPS vs Resource Diversity\nColored by Local Win Rate')
    fig.tight_layout()
    fig.savefig(os.path.join(RESULTS_DIR, 'score_frontier.png'), dpi=150)
    plt.close(fig)
    print('  saved score_frontier.png')


if __name__ == '__main__':
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f'Running {N_GAMES} simulations...')
    df = run_simulation(N_GAMES)
    print(f'Simulation complete. {len(df)} player records.')
    print(df[['SNPS', 'ANPS', 'PSS', 'resource_diversity', 'win']].describe().round(2))

    print('\nGenerating charts...')
    plot_scoring_comparison(df)
    plot_winrate_by_metric(df, 'SNPS', 'winrate_by_snps.png')
    plot_winrate_by_metric(df, 'ANPS', 'winrate_by_anps.png')
    plot_winrate_by_metric(df, 'PSS', 'winrate_by_pss.png')
    plot_turn_order_scores(df)
    plot_score_frontier(df)

    print(f'\nAll charts saved to {os.path.abspath(RESULTS_DIR)}')
