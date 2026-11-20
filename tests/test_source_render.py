"""Tests for local dependency input and graph output formats."""

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree
from zipfile import ZipFile

from dependency_visualizer.graph import build_graph
from dependency_visualizer.render import node_id, save_plantuml, save_svg
from dependency_visualizer.source import (
    NuGetSource,
    TestGraphSource,
    compare_versions,
    nuspec_from_archive,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class SourceAndRenderTests(unittest.TestCase):
    """Verify test repository parsing and graph serialization."""

    def test_reads_test_graph_fixture(self) -> None:
        """Load direct dependencies from the uppercase TOML fixture."""
        source = TestGraphSource(str(FIXTURE_DIR / "test_graph_chain.toml"))

        self.assertEqual(source.direct_dependencies("A"), ["B"])
        self.assertEqual(source.direct_dependencies("C"), [])

    def test_rejects_unknown_dependency(self) -> None:
        """Require test graph references to name declared packages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            graph_path = Path(temp_dir) / "bad.toml"
            graph_path.write_text(
                '[packages]\nA = ["B"]\n', encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "Unknown dependency"):
                TestGraphSource(str(graph_path))

    def test_compares_stable_version_components(self) -> None:
        """Compare dotted numeric NuGet versions numerically."""
        self.assertGreater(compare_versions("2.10.0", "2.9.9"), 0)
        self.assertEqual(compare_versions("1.0", "1.0.0"), 0)

    def test_extracts_dependencies_from_nuspec_xml(self) -> None:
        """Read dependency IDs from namespaced nuspec metadata."""
        source = object.__new__(NuGetSource)
        xml_data = (
            '<package xmlns="urn:test"><metadata><dependencies>'
            '<group><dependency id="Alpha" version="1.0"/>'
            '<dependency id="Beta" version="2.0"/></group>'
            '</dependencies></metadata></package>'
        )

        dependencies = source._parse_nuspec(xml_data)

        self.assertEqual(dependencies, ["Alpha", "Beta"])

    def test_extracts_nuspec_from_package_archive(self) -> None:
        """Read nuspec XML from an in-memory package archive."""
        package_data = BytesIO()
        with ZipFile(package_data, "w") as archive:
            archive.writestr(
                "Example.nuspec",
                '<package><metadata><dependencies>'
                '<dependency id="Alpha" version="1.0"/>'
                '</dependencies></metadata></package>',
            )

        nuspec = nuspec_from_archive(package_data.getvalue())

        self.assertIn('id="Alpha"', nuspec)

    def test_writes_plantuml_and_svg_in_new_directory(self) -> None:
        """Create both graph formats and parse the SVG as valid XML."""
        graph = build_graph("A", lambda _package: ["B"], "")
        with tempfile.TemporaryDirectory() as temp_dir:
            svg_path = Path(temp_dir) / "nested" / "graph.svg"
            plantuml_path = save_plantuml(graph, str(svg_path))
            saved_svg = save_svg(graph, str(svg_path))

            self.assertTrue(plantuml_path.is_file())
            self.assertIn("@startuml", plantuml_path.read_text())
            self.assertTrue(saved_svg.is_file())
            ElementTree.parse(saved_svg)

    def test_plantuml_ids_are_unique_for_distinct_names(self) -> None:
        """Keep package names A-B and A_B as separate PlantUML vertices."""
        graph_data = {"root": ["A-B", "A_B"], "A-B": [], "A_B": []}
        graph = build_graph("root", graph_data.__getitem__, "")

        self.assertNotEqual(node_id("A-B"), node_id("A_B"))
        with tempfile.TemporaryDirectory() as temp_dir:
            path = save_plantuml(
                graph, str(Path(temp_dir) / "collision.svg")
            )
            plantuml = path.read_text(encoding="utf-8")

        self.assertIn('component "A-B" as package_412d42', plantuml)
        self.assertIn('component "A_B" as package_415f42', plantuml)
        self.assertIn(
            f"{node_id('root')} --> {node_id('A-B')}", plantuml
        )
        self.assertIn(
            f"{node_id('root')} --> {node_id('A_B')}", plantuml
        )


if __name__ == "__main__":
    unittest.main()
