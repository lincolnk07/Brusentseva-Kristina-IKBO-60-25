"""Render PlantUML source, SVG graphs, and dependency reports."""

from html import escape
from pathlib import Path

from dependency_visualizer.graph import DependencyGraph


NODE_WIDTH = 180
NODE_HEIGHT = 52
HORIZONTAL_GAP = 90
VERTICAL_GAP = 34
MARGIN = 30


def plantuml_text(graph: DependencyGraph) -> str:
    """Return a PlantUML description for the directed dependency graph."""
    lines = [
        "@startuml",
        "left to right direction",
        "skinparam linetype ortho",
    ]
    for package in sorted(graph.edges, key=str.casefold):
        lines.append(f'component "{escape(package)}" as {node_id(package)}')
    for package, dependencies in sorted(graph.edges.items()):
        for dependency in dependencies:
            lines.append(f"{node_id(package)} --> {node_id(dependency)}")
    lines.append("@enduml")
    return "\n".join(lines) + "\n"


def save_plantuml(graph: DependencyGraph, output_path: str) -> Path:
    """Save the PlantUML source alongside the generated SVG."""
    path = Path(output_path).with_suffix(".puml")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plantuml_text(graph), encoding="utf-8")
    return path


def save_svg(graph: DependencyGraph, output_path: str) -> Path:
    """Create a dependency graph SVG using only the Python standard library."""
    levels = graph_levels(graph)
    positions = layout_nodes(levels)
    width, height = canvas_size(levels)
    elements = svg_header(width, height)
    elements.extend(edge_elements(graph, positions))
    elements.extend(node_elements(graph, positions))
    elements.append("</svg>")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")
    return path


def node_id(package: str) -> str:
    """Create a collision-free PlantUML identifier from UTF-8 bytes."""
    return "package_" + package.encode("utf-8").hex()


def graph_levels(graph: DependencyGraph) -> dict[str, int]:
    """Assign each package a display level with recursive traversal."""
    levels = {graph.root: 0}

    def visit(package: str, level: int, ancestors: set[str]) -> None:
        """Assign levels while preventing loops on cyclic edges."""
        for dependency in graph.edges.get(package, []):
            if dependency in ancestors:
                continue
            next_level = level + 1
            if next_level > levels.get(dependency, -1):
                levels[dependency] = next_level
                visit(dependency, next_level, ancestors | {dependency})

    visit(graph.root, 0, {graph.root})
    for package in graph.edges:
        levels.setdefault(package, 0)
    return levels


def layout_nodes(levels: dict[str, int]) -> dict[str, tuple[int, int]]:
    """Place packages in columns by graph level."""
    columns: dict[int, list[str]] = {}
    for package, level in levels.items():
        columns.setdefault(level, []).append(package)
    positions = {}
    for level, packages in columns.items():
        for row, package in enumerate(sorted(packages, key=str.casefold)):
            x = MARGIN + level * (NODE_WIDTH + HORIZONTAL_GAP)
            y = MARGIN + row * (NODE_HEIGHT + VERTICAL_GAP)
            positions[package] = (x, y)
    return positions


def canvas_size(levels: dict[str, int]) -> tuple[int, int]:
    """Calculate SVG dimensions for the package layout."""
    max_level = max(levels.values(), default=0)
    counts = [
        sum(value == level for value in levels.values())
        for level in set(levels.values())
    ]
    max_column = max(counts, default=1)
    width = (
        2 * MARGIN
        + (max_level + 1) * NODE_WIDTH
        + max_level * HORIZONTAL_GAP
    )
    height = (
        2 * MARGIN
        + max_column * NODE_HEIGHT
        + (max_column - 1) * VERTICAL_GAP
    )
    return width, height


def svg_header(width: int, height: int) -> list[str]:
    """Return the opening SVG and its lightweight style declarations."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]


def edge_elements(
    graph: DependencyGraph, positions: dict[str, tuple[int, int]]
) -> list[str]:
    """Return SVG line elements for all directed dependency edges."""
    elements = ['<g fill="none" stroke="#52627a" stroke-width="2">']
    for package, dependencies in graph.edges.items():
        for dependency in dependencies:
            start_x, start_y = positions[package]
            end_x, end_y = positions[dependency]
            x1 = start_x + NODE_WIDTH
            y1 = start_y + NODE_HEIGHT // 2
            x2 = end_x
            y2 = end_y + NODE_HEIGHT // 2
            elements.append(
                f'<path d="M {x1} {y1} C {x1 + 35} {y1}, '
                f'{x2 - 35} {y2}, {x2} {y2}" '
                'marker-end="url(#arrow)"/>'
            )
    elements.extend(["</g>", arrow_marker()])
    return elements


def arrow_marker() -> str:
    """Return an SVG arrow marker definition."""
    return (
        '<defs><marker id="arrow" markerWidth="10" '
        'markerHeight="10" refX="8" refY="3" orient="auto">'
        '<path d="M0,0 L0,6 L9,3 z" '
        'fill="#52627a"/></marker></defs>'
    )


def node_elements(
    graph: DependencyGraph, positions: dict[str, tuple[int, int]]
) -> list[str]:
    """Return SVG rectangles and labels for every package."""
    elements = []
    for package, (x_pos, y_pos) in positions.items():
        label = escape(package)
        elements.append(
            f'<rect x="{x_pos}" y="{y_pos}" '
            f'width="{NODE_WIDTH}" '
            f'height="{NODE_HEIGHT}" rx="8" fill="#eef4ff" '
            'stroke="#2f5d9b" stroke-width="2"/>'
        )
        elements.append(
            f'<text x="{x_pos + NODE_WIDTH // 2}" '
            f'y="{y_pos + NODE_HEIGHT // 2 + 5}" '
            'text-anchor="middle" '
            'font-family="sans-serif" font-size="14" fill="#172b4d">'
            f"{label}</text>"
        )
    return elements
