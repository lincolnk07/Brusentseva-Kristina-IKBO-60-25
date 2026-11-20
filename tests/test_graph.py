"""Tests for recursive graph traversal, filtering, cycles, and ordering."""

import unittest

from dependency_visualizer.graph import ascii_tree, build_graph


GRAPH_DATA = {
    "A": ["B", "C"],
    "B": ["D"],
    "C": ["D"],
    "D": [],
}


def dependencies_for(package: str) -> list[str]:
    """Return fixture dependencies for one graph vertex."""
    return GRAPH_DATA[package]


class GraphTests(unittest.TestCase):
    """Verify graph building behavior for required graph cases."""

    def test_builds_transitive_graph_and_load_order(self) -> None:
        """Visit transitive packages once and place dependencies first."""
        graph = build_graph("A", dependencies_for, "")

        self.assertEqual(set(graph.edges), {"A", "B", "C", "D"})
        self.assertEqual(graph.load_order, ["D", "B", "C", "A"])
        self.assertEqual(graph.cycles, [])

    def test_chain_order_includes_root_last(self) -> None:
        """List C, B, A for the chain A -> B -> C."""
        chain = {"A": ["B"], "B": ["C"], "C": []}
        graph = build_graph("A", chain.__getitem__, "")

        self.assertEqual(graph.load_order, ["C", "B", "A"])

    def test_excludes_names_containing_filter(self) -> None:
        """Remove filtered packages and their outgoing edges."""
        graph = build_graph("A", dependencies_for, "B")

        self.assertEqual(graph.edges["A"], ["C"])
        self.assertNotIn("B", graph.edges)
        self.assertNotIn("B", graph.load_order)

    def test_detects_cycle(self) -> None:
        """Record a back edge without recursing forever."""
        cycle_graph = {"A": ["B"], "B": ["D"], "D": ["A"]}
        graph = build_graph("A", cycle_graph.__getitem__, "")

        self.assertEqual(graph.cycles, [("D", "A")])
        self.assertEqual(set(graph.edges), {"A", "B", "D"})

    def test_ascii_tree_marks_cycle(self) -> None:
        """Show the cycle edge in the tree representation."""
        cycle_graph = {"A": ["B"], "B": ["A"]}
        graph = build_graph("A", cycle_graph.__getitem__, "")

        self.assertEqual(ascii_tree(graph), "A\n`-- B\n    `-- A [cycle]")

    def test_filtered_root_has_no_dependencies(self) -> None:
        """Avoid traversing a root that itself matches the filter."""
        graph = build_graph("A", dependencies_for, "A")

        self.assertEqual(graph.edges, {"A": []})
        self.assertEqual(graph.load_order, ["A"])


if __name__ == "__main__":
    unittest.main()
