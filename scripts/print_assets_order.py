"""Print a dependency-first order derived from a NuGet assets file."""

import argparse
import json
from pathlib import Path


def dependency_first_order(assets: dict, framework: str) -> list[str]:
    """Return one deterministic order for resolved package dependencies."""
    target_graph = assets.get("targets", {}).get(framework)
    framework_data = assets.get("project", {}).get("frameworks", {}).get(
        framework
    )
    if target_graph is None or framework_data is None:
        raise ValueError(f"Target framework {framework!r} is absent")

    package_names = {
        key.rsplit("/", maxsplit=1)[0]: entry
        for key, entry in target_graph.items()
        if entry.get("type") == "package"
    }
    canonical_names = {
        package.casefold(): package for package in package_names
    }
    edges = {}
    for package, entry in package_names.items():
        dependencies = entry.get("dependencies", {})
        edges[package] = sorted(
            {
                canonical_names[name.casefold()]
                for name in dependencies
                if name.casefold() in canonical_names
            },
            key=str.casefold,
        )

    direct_dependencies = framework_data.get("dependencies", {})
    roots = sorted(
        {
            canonical_names[name.casefold()]
            for name in direct_dependencies
            if name.casefold() in canonical_names
        },
        key=str.casefold,
    )
    state = {}
    order = []

    def visit(package: str) -> None:
        """Visit dependencies before appending their package."""
        if state.get(package) == "active":
            raise ValueError(f"Cycle in resolved assets graph at {package}")
        if state.get(package) == "done":
            return
        state[package] = "active"
        for dependency in edges[package]:
            visit(dependency)
        state[package] = "done"
        order.append(package)

    for package in roots:
        visit(package)
    return order


def main() -> int:
    """Read an assets file and print its resolved package order."""
    parser = argparse.ArgumentParser()
    parser.add_argument("assets_file", type=Path)
    parser.add_argument("framework")
    options = parser.parse_args()
    try:
        assets = json.loads(options.assets_file.read_text(encoding="utf-8"))
        order = dependency_first_order(assets, options.framework)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        parser.error(str(error))
    print(f"Resolved package count: {len(order)}")
    print("Dependency-first order derived from project.assets.json:")
    print(", ".join(order) if order else "(no resolved package dependencies)")
    print("This is a graph-derived order, not a NuGet loading sequence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
