"""Build dependency graphs and calculate dependency-first order."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class DependencyGraph:
    """Directed dependency graph and cycles found during depth-first search."""

    root: str
    edges: dict[str, list[str]]
    cycles: list[tuple[str, str]]
    load_order: list[str]


def build_graph(
    root: str,
    read_dependencies: Callable[[str], list[str]],
    filter_substring: str,
) -> DependencyGraph:
    """Build a transitive graph using recursive depth-first search."""
    edges: dict[str, list[str]] = {}
    cycles: list[tuple[str, str]] = []
    visited_nodes: set[str] = set()
    active_nodes: set[str] = set()
    load_order: list[str] = []

    def visit(package: str) -> None:
        """Visit one package recursively and record dependency edges."""
        if package in visited_nodes or package in active_nodes:
            return
        active_nodes.add(package)
        dependencies = read_dependencies(package)
        included = [
            name for name in dependencies
            if not filter_substring or filter_substring not in name
        ]
        edges[package] = sorted(set(included), key=str.casefold)
        for dependency in edges[package]:
            if dependency in active_nodes:
                cycles.append((package, dependency))
            elif dependency not in visited_nodes:
                visit(dependency)
        active_nodes.remove(package)
        visited_nodes.add(package)
        load_order.append(package)

    if filter_substring and filter_substring in root:
        edges[root] = []
        load_order.append(root)
    else:
        visit(root)
    return DependencyGraph(root, edges, cycles, load_order)


def ascii_tree(graph: DependencyGraph) -> str:
    """Format a dependency graph as an ASCII tree."""
    lines = [graph.root]

    def append_children(
        package: str, prefix: str, ancestors: set[str]
    ) -> None:
        """Append a package's children while marking cycles and duplicates."""
        dependencies = graph.edges.get(package, [])
        for index, dependency in enumerate(dependencies):
            last_child = index == len(dependencies) - 1
            branch = "`-- " if last_child else "|-- "
            marker = (
                " [cycle]" if dependency in ancestors else ""
            )
            lines.append(prefix + branch + dependency + marker)
            if dependency not in ancestors:
                extension = "    " if last_child else "|   "
                append_children(
                    dependency,
                    prefix + extension,
                    ancestors | {dependency},
                )

    append_children(graph.root, "", {graph.root})
    return "\n".join(lines)
