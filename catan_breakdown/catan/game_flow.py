from __future__ import annotations
from catan.board import CatanBoard


class SnakeDraft:
    """Manages snake-draft initial settlement placement for 2-4 players.

    Turn order: forward (0→N-1) then reversed (N-1→0), so each player picks twice.
    Example (4p): [0, 1, 2, 3, 3, 2, 1, 0]
    """

    def __init__(self, num_players: int, board: CatanBoard) -> None:
        if num_players not in {2, 3, 4}:
            raise ValueError(f"num_players must be 2, 3, or 4; got {num_players}")
        self.num_players = num_players
        self.board = board
        self.turn_order: list[int] = (
            list(range(num_players)) + list(reversed(range(num_players)))
        )
        self.current_pick: int = 0
        self.done: bool = False
        self.placements: dict[int, list[int]] = {i: [] for i in range(num_players)}

    @property
    def current_player(self) -> int:
        return self.turn_order[self.current_pick]

    def is_first_placement(self) -> bool:
        return len(self.placements[self.current_player]) == 0

    def valid_placements(self) -> list[int]:
        all_placed = [n for nodes in self.placements.values() for n in nodes]
        return self.board.valid_placements(all_placed)

    def place(self, node_id: int) -> dict[str, int] | None:
        """Place a settlement for the current player.

        Returns starting resources (1 card per adjacent non-desert hex) if this
        is the player's second placement, otherwise None.
        Raises ValueError for invalid placement or if the draft is already complete.
        """
        if self.done:
            raise ValueError("Draft is already complete")
        if node_id not in self.valid_placements():
            raise ValueError(f"Node {node_id} is not a valid placement")

        player = self.current_player
        self.placements[player].append(node_id)
        is_second = len(self.placements[player]) == 2
        starting = self._starting_resources(node_id) if is_second else None

        self.current_pick += 1
        if self.current_pick == len(self.turn_order):
            self.done = True

        return starting

    def _starting_resources(self, node_id: int) -> dict[str, int]:
        resources: dict[str, int] = {}
        for num, res in self.board.settlement_dict[node_id]['numres']:
            if num != 0:  # desert tiles have num=0
                resources[res] = resources.get(res, 0) + 1
        return resources
