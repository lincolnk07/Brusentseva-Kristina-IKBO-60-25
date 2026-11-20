"""Tests for deriving a dependency-first order from NuGet restore assets."""

import unittest

from scripts.print_assets_order import dependency_first_order


class AssetsOrderTests(unittest.TestCase):
    """Verify ordering over the package graph emitted by NuGet restore."""

    def test_orders_transitive_package_before_its_dependency(self) -> None:
        """Put package C before B when the restored edge is B -> C."""
        assets = {
            "targets": {
                "net8.0": {
                    "B/2.0.0": {
                        "type": "package",
                        "dependencies": {"C": "[1.0.0, )"},
                    },
                    "C/1.0.0": {"type": "package"},
                }
            },
            "project": {
                "frameworks": {
                    "net8.0": {
                        "dependencies": {"B": {"target": "Package"}}
                    }
                }
            },
        }

        self.assertEqual(
            dependency_first_order(assets, "net8.0"), ["C", "B"]
        )

    def test_rejects_missing_target_framework(self) -> None:
        """Require assets to contain the selected target framework."""
        with self.assertRaisesRegex(ValueError, "is absent"):
            dependency_first_order({}, "net8.0")


if __name__ == "__main__":
    unittest.main()
