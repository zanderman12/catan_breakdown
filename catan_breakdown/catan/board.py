import random
import itertools
import numpy as np

# Settlement node adjacency (which of the 54 nodes are direct neighbors).
# Derived from hex tile topology: each tile's 6 vertices listed clockwise,
# consecutive pairs (including wrap) are edges.
ADJACENCY = {
    1:  [2, 9],
    2:  [1, 3],
    3:  [2, 4, 11],
    4:  [3, 5],
    5:  [4, 6, 13],
    6:  [5, 7],
    7:  [6, 15],
    8:  [9, 18],
    9:  [1, 8, 10],
    10: [9, 11, 20],
    11: [3, 10, 12],
    12: [11, 13, 22],
    13: [5, 12, 14],
    14: [13, 15, 24],
    15: [7, 14, 16],
    16: [15, 26],
    17: [18, 28],
    18: [8, 17, 19],
    19: [18, 20, 30],
    20: [10, 19, 21],
    21: [20, 22, 32],
    22: [12, 21, 23],
    23: [22, 24, 34],
    24: [14, 23, 25],
    25: [24, 26, 36],
    26: [16, 25, 27],
    27: [26, 38],
    28: [17, 29],
    29: [28, 30, 39],
    30: [19, 29, 31],
    31: [30, 32, 41],
    32: [21, 31, 33],
    33: [32, 34, 43],
    34: [23, 33, 35],
    35: [34, 36, 45],
    36: [25, 35, 37],
    37: [36, 38, 47],
    38: [27, 37],
    39: [29, 40],
    40: [39, 41, 48],
    41: [31, 40, 42],
    42: [41, 43, 50],
    43: [33, 42, 44],
    44: [43, 45, 52],
    45: [35, 44, 46],
    46: [45, 47, 54],
    47: [37, 46],
    48: [40, 49],
    49: [48, 50],
    50: [42, 49, 51],
    51: [50, 52],
    52: [44, 51, 53],
    53: [52, 54],
    54: [46, 53],
}

# (col, row) integer grid coordinates for each node.
# Within a row nodes are spaced 2 apart; cross-row neighbors differ by 1 in col
# and 1 in row — matches the flat-top hex grid topology.
NODE_COORDS = {
    # row 0 (top, 7 nodes)
    1:  (0,  0), 2:  (2,  0), 3:  (4,  0), 4:  (6,  0),
    5:  (8,  0), 6:  (10, 0), 7:  (12, 0),
    # row 1 (9 nodes)
    8:  (-1, 1), 9:  (1,  1), 10: (3,  1), 11: (5,  1),
    12: (7,  1), 13: (9,  1), 14: (11, 1), 15: (13, 1), 16: (15, 1),
    # row 2 (11 nodes)
    17: (-2, 2), 18: (0,  2), 19: (2,  2), 20: (4,  2), 21: (6,  2),
    22: (8,  2), 23: (10, 2), 24: (12, 2), 25: (14, 2), 26: (16, 2), 27: (18, 2),
    # row 3 (11 nodes)
    28: (-1, 3), 29: (1,  3), 30: (3,  3), 31: (5,  3), 32: (7,  3),
    33: (9,  3), 34: (11, 3), 35: (13, 3), 36: (15, 3), 37: (17, 3), 38: (19, 3),
    # row 4 (9 nodes)
    39: (2,  4), 40: (4,  4), 41: (6,  4), 42: (8,  4), 43: (10, 4),
    44: (12, 4), 45: (14, 4), 46: (16, 4), 47: (18, 4),
    # row 5 (bottom, 7 nodes)
    48: (3,  5), 49: (5,  5), 50: (7,  5), 51: (9,  5),
    52: (11, 5), 53: (13, 5), 54: (15, 5),
}


def _create_board():
    tile_types = ['desert', 'sheep', 'sheep', 'sheep', 'sheep',
                  'wood', 'wood', 'wood', 'wood', 'wheat',
                  'wheat', 'wheat', 'wheat', 'brick', 'brick',
                  'brick', 'ore', 'ore', 'ore']
    tile_nums = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]

    random.shuffle(tile_types)
    random.shuffle(tile_nums)

    tile_dict = {}
    num_dict = {}
    num_counter = 0

    for i, t in enumerate(tile_types):
        tile_num = tile_nums[num_counter] if t != 'desert' else 0
        if t != 'desert':
            num_counter += 1

        tile_dict[i] = {'resource': t, 'num': tile_num}
        num_dict.setdefault(tile_num, []).append(i)

    return tile_dict, num_dict


def _res_availability(tile_dict, pipdict):
    avail = {'wood': 0, 'brick': 0, 'ore': 0, 'sheep': 0, 'wheat': 0}
    for t in tile_dict.values():
        if t['resource'] != 'desert':
            avail[t['resource']] += pipdict[t['num']]
    return avail


def _build_settlement_dict(tile_dict, pipdict):
    """Build the 54-node settlement graph with resources, ports, and pip values."""
    settlement_dict = {
        1:  {'tiles': [0]},          2:  {'tiles': [0]},
        3:  {'tiles': [0, 1]},       4:  {'tiles': [1]},
        5:  {'tiles': [1, 2]},       6:  {'tiles': [2]},
        7:  {'tiles': [2]},
        8:  {'tiles': [3]},          9:  {'tiles': [0, 3]},
        10: {'tiles': [0, 3, 4]},    11: {'tiles': [0, 1, 4]},
        12: {'tiles': [1, 4, 5]},    13: {'tiles': [1, 2, 5]},
        14: {'tiles': [2, 5, 6]},    15: {'tiles': [2, 6]},
        16: {'tiles': [6]},
        17: {'tiles': [7]},          18: {'tiles': [3, 7]},
        19: {'tiles': [3, 7, 8]},    20: {'tiles': [3, 4, 8]},
        21: {'tiles': [4, 8, 9]},    22: {'tiles': [4, 5, 9]},
        23: {'tiles': [5, 9, 10]},   24: {'tiles': [5, 6, 10]},
        25: {'tiles': [6, 10, 11]},  26: {'tiles': [6, 11]},
        27: {'tiles': [11]},
        28: {'tiles': [7]},          29: {'tiles': [7, 12]},
        30: {'tiles': [7, 8, 12]},   31: {'tiles': [8, 12, 13]},
        32: {'tiles': [8, 9, 13]},   33: {'tiles': [9, 13, 14]},
        34: {'tiles': [9, 10, 14]},  35: {'tiles': [10, 14, 15]},
        36: {'tiles': [10, 11, 15]}, 37: {'tiles': [11, 15]},
        38: {'tiles': [11]},
        39: {'tiles': [12]},         40: {'tiles': [12, 16]},
        41: {'tiles': [12, 13, 16]}, 42: {'tiles': [13, 16, 17]},
        43: {'tiles': [13, 14, 17]}, 44: {'tiles': [14, 17, 18]},
        45: {'tiles': [14, 15, 18]}, 46: {'tiles': [15, 18]},
        47: {'tiles': [15]},
        48: {'tiles': [16]},         49: {'tiles': [16]},
        50: {'tiles': [16, 17]},     51: {'tiles': [17]},
        52: {'tiles': [17, 18]},     53: {'tiles': [18]},
        54: {'tiles': [18]},
    }

    # Assign ports
    port_locs = {
        0: [1, 2], 1: [4, 5], 2: [15, 16], 3: [27, 38], 4: [46, 47],
        5: [51, 52], 6: [48, 49], 7: [29, 39], 8: [8, 18],
    }
    port_types = ['brick', 'sheep', 'wood', 'wheat', 'ore', 'any', 'any', 'any', 'any']
    random.shuffle(port_types)
    for i, p in enumerate(port_types):
        for s in port_locs[i]:
            settlement_dict[s]['port'] = p
    for s in settlement_dict:
        settlement_dict[s].setdefault('port', None)

    # Compute port values
    res_avail = _res_availability(tile_dict, pipdict)
    resvalue_dict = {
        'wood':  3.86 - 0.178 * res_avail['wood'],
        'brick': 3.72 - 0.18  * res_avail['brick'],
        'sheep': 3.22 - 0.19  * res_avail['sheep'],
        'wheat': 3.75 - 0.15  * res_avail['wheat'],
        'ore':   2.98 - 0.12  * res_avail['ore'],
    }

    port_value_dict = {}
    fourone_vals, threeone_vals = [], []
    for combo in itertools.combinations(list(resvalue_dict.keys()), 4):
        val = sum(resvalue_dict[r] for r in combo)
        fourone_vals.append(val / 16)
        threeone_vals.append(val / 12)
        for res in resvalue_dict:
            if res not in combo:
                port_value_dict[res] = val / 8
    port_value_dict[None] = np.mean(fourone_vals)
    port_value_dict['any'] = np.mean(threeone_vals)

    # Simulate roll distribution for resource counting
    game_len = 72
    rolls = np.array([2, 3, 4, 5, 6, 8, 9, 10, 11, 12])
    full_rolls = np.append(rolls, np.sum(np.random.randint(1, 7, (game_len, 2)), axis=1))
    unique_rolls, roll_counts = np.unique(full_rolls, return_counts=True)
    roll_counts = roll_counts - 1

    for s, data in settlement_dict.items():
        data['resources'] = {'wood': 0, 'sheep': 0, 'brick': 0, 'wheat': 0, 'ore': 0}
        data['numres'] = []
        data['port_value'] = port_value_dict[data['port']]

        for t in data['tiles']:
            res = tile_dict[t]['resource']
            num = tile_dict[t]['num']
            data['numres'].append((num, res))
            if num != 0:
                count = roll_counts[np.argwhere(unique_rolls == num)][0, 0]
                data['resources'][res] += count

    return settlement_dict, resvalue_dict, res_avail


class CatanBoard:
    """Randomized Catan board with 54-node settlement graph and scoring helpers."""

    PIPDICT = {0: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

    def __init__(self):
        self.tile_dict, self.num_dict = _create_board()
        self.pipdict = self.PIPDICT
        self.settlement_dict, self.resvalue_dict, self.res_availability_dict = (
            _build_settlement_dict(self.tile_dict, self.pipdict)
        )
        self.adjacency = ADJACENCY
        self.node_coords = NODE_COORDS

    def valid_placements(self, placed: list) -> list:
        """Return all legal node ids given already-placed settlements (any player's)."""
        excluded = set(placed)
        for node in placed:
            excluded.update(self.adjacency[node])
        return [n for n in self.settlement_dict if n not in excluded]

    def pip_count(self, node_id: int) -> int:
        """Total pip value (roll probability) for a settlement at node_id."""
        return sum(self.pipdict[num] for num, _res in self.settlement_dict[node_id]['numres'])

    def resource_score(self, node_id: int) -> float:
        """Board-adjusted weighted resource score for a settlement at node_id."""
        res = self.settlement_dict[node_id]['resources']
        rv = self.resvalue_dict
        return float(np.sum([
            res['wood']  * rv['wood'],
            res['brick'] * rv['brick'],
            res['sheep'] * rv['sheep'],
            res['wheat'] * rv['wheat'],
            res['ore']   * rv['ore'],
        ]))
