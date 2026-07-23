import math


def pointy_top_hex_vertices(cx, cy, size):
    """Return the 6 vertices of a pointy-top hexagon centered at (cx, cy)."""
    return [
        (
            cx + size * math.cos(math.radians(60 * i - 30)),
            cy + size * math.sin(math.radians(60 * i - 30)),
        )
        for i in range(6)
    ]


def generate_hex_grid_vertices(row_counts, size=1.0):
    """
    Collect all unique vertex coordinates for a pointy-top hexagonal grid,
    centered at the origin.

    row_counts : list of ints — number of hexagons in each row (bottom to top)
    size       : circumradius (center-to-vertex distance) of each hexagon
    """
    h_spacing = math.sqrt(3) * size  # horizontal center-to-center distance
    v_spacing = 1.5 * size           # vertical center-to-center distance

    num_rows = len(row_counts)

    # Center each row at x=0. When adjacent rows differ by 1 hex (e.g. Catan),
    # the centering naturally produces the √3/2 horizontal stagger required for
    # edge-sharing. For uniform row counts you would need an explicit offset.
    centers = []
    for row, count in enumerate(row_counts):
        raw_cy = row * v_spacing
        x_start = -(count - 1) * h_spacing / 2
        for col in range(count):
            centers.append((x_start + col * h_spacing, raw_cy))

    # Shift vertically so the grid is centered at y=0
    cy_mid = (num_rows - 1) * v_spacing / 2
    centers = [(cx, cy - cy_mid) for cx, cy in centers]

    # Collect unique vertices (round to 8 dp to collapse floating-point dupes)
    vertices = set()
    for cx, cy in centers:
        for vx, vy in pointy_top_hex_vertices(cx, cy, size):
            vertices.add((round(vx, 8), round(vy, 8)))

    # Sort bottom-to-top, left-to-right
    return sorted(vertices, key=lambda p: (round(p[1], 6), round(p[0], 6)))


def main():
    raw = input("Hexagons per row (space-separated, bottom to top): ").strip()
    row_counts = [int(x) for x in raw.split()]
    size_input = input("Hex size / circumradius [1.0]: ").strip()
    size = float(size_input) if size_input else 1.0

    verts = generate_hex_grid_vertices(row_counts, size)

    print(f"\n{len(verts)} unique vertices (sorted bottom to top, left to right):\n")
    for x, y in verts:
        print(f"  ({x:>12.6f},  {y:>12.6f})")


if __name__ == "__main__":
    main()
