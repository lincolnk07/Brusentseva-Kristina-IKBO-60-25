"""Tests for TOML settings and parameter validation."""

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from dependency_visualizer.cli import print_settings
from dependency_visualizer.config import (
    Settings,
    load_settings,
    validate_settings,
)


class ConfigTests(unittest.TestCase):
    """Verify the six required configuration parameters."""

    def setUp(self) -> None:
        """Create a valid temporary test repository and settings object."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.graph_path = Path(self.temp_dir.name) / "graph.toml"
        self.graph_path.write_text(
            '[packages]\nA = []\n', encoding="utf-8"
        )
        self.settings = Settings(
            package_name="A",
            repository_url=str(self.graph_path),
            test_repository=True,
            graph_file="graph.svg",
            ascii_tree=False,
            filter_substring="",
        )

    def tearDown(self) -> None:
        """Remove temporary files."""
        self.temp_dir.cleanup()

    def test_loads_all_six_parameters(self) -> None:
        """Load every user-configurable field from a TOML file."""
        config_path = Path(self.temp_dir.name) / "config.toml"
        config_path.write_text(
            f'package_name = "A"\n'
            f'repository_url = "{self.graph_path}"\n'
            "test_repository = true\n"
            'graph_file = "graph.svg"\n'
            "ascii_tree = false\n"
            'filter_substring = ""\n',
            encoding="utf-8",
        )

        loaded = load_settings(str(config_path))

        self.assertEqual(loaded, self.settings)

    def test_prints_all_six_parameters(self) -> None:
        """Print each user-configurable setting as a key-value pair."""
        from contextlib import redirect_stdout
        from io import StringIO

        output = StringIO()
        with redirect_stdout(output):
            print_settings(self.settings)

        printed_keys = [line.split(" = ", maxsplit=1)[0]
                        for line in output.getvalue().splitlines()]
        self.assertEqual(len(printed_keys), 6)
        self.assertEqual(set(printed_keys), {
            "package_name",
            "repository_url",
            "test_repository",
            "graph_file",
            "ascii_tree",
            "filter_substring",
        })

    def test_rejects_invalid_parameter_values(self) -> None:
        """Reject invalid values for each of the six settings."""
        invalid_values = [
            ("package_name", ""),
            ("repository_url", ""),
            ("test_repository", 1),
            ("graph_file", "graph.png"),
            ("ascii_tree", "false"),
            ("filter_substring", 7),
        ]
        for field_name, value in invalid_values:
            with self.subTest(field=field_name):
                invalid_settings = replace(
                    self.settings, **{field_name: value}
                )
                with self.assertRaises(ValueError):
                    validate_settings(invalid_settings)

    def test_rejects_invalid_http_url(self) -> None:
        """Require HTTP or HTTPS URLs outside test mode."""
        invalid_settings = replace(
            self.settings,
            repository_url="ftp://example.org/nuget",
            test_repository=False,
        )

        with self.assertRaisesRegex(ValueError, "HTTP or HTTPS"):
            validate_settings(invalid_settings)

    def test_rejects_missing_test_graph(self) -> None:
        """Require an existing local graph file in test mode."""
        invalid_settings = replace(
            self.settings,
            repository_url=str(Path(self.temp_dir.name) / "missing.toml"),
        )

        with self.assertRaisesRegex(ValueError, "does not exist"):
            validate_settings(invalid_settings)


if __name__ == "__main__":
    unittest.main()
