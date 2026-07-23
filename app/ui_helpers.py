"""Formatting helpers for the Streamlit sidebar."""
from collections import Counter

import pandas as pd

_RES_ABBREV: dict[str, str] = {
    "wood": "WD", "brick": "BK", "ore": "OR",
    "sheep": "SH", "wheat": "WH", "desert": "--",
}

_PORT_LABEL: dict[str, str] = {
    "wood": "WD 2:1", "brick": "BK 2:1", "ore": "OR 2:1",
    "sheep": "SH 2:1", "wheat": "WH 2:1", "any": "3:1",
}


def format_score_table(sc: dict) -> pd.DataFrame:
    return pd.DataFrame([
        {"Metric": "Pips",           "Value": str(sc["pips"])},
        {"Metric": "Resource Score", "Value": f"{sc['resource_score']:.2f}"},
        {"Metric": "Port Value",     "Value": f"{sc['port_value']:.2f}"},
        {"Metric": "Diversity",      "Value": f"{sc['diversity_score']:.2f}"},
        {"Metric": "Port Synergy",   "Value": f"{sc['port_synergy']:.2f}"},
        {"Metric": "Composite",      "Value": f"{sc['composite_score']:.2f}"},
    ])


def format_starting_hand(node_id: int, board) -> str:
    """Resources received when placing the 2nd settlement on node_id."""
    s = board.settlement_dict[node_id]
    abbrevs = [
        _RES_ABBREV.get(res, res)
        for num, res in s["numres"]
        if res != "desert" and num != 0
    ]
    if not abbrevs:
        return "none"
    counts = Counter(abbrevs)
    return ", ".join(f"{cnt}×{res}" for res, cnt in sorted(counts.items()))


def port_label(port: str) -> str:
    return _PORT_LABEL.get(port, port)


def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    return f"{n}{['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]}"
