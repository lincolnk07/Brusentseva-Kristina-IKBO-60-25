"""Command-line interface for recursive dependency graph construction."""

import argparse
import sys

from dependency_visualizer.config import load_settings
from dependency_visualizer.graph import build_graph
from dependency_visualizer.source import NuGetSource, TestGraphSource


def main(arguments: list[str] | None = None) -> int:
    """Run one of the first three stages."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), default=3)
    options = parser.parse_args(arguments)
    try:
        settings = load_settings(options.config)
        if options.stage == 1:
            for key, value in settings.__dict__.items():
                print(f"{key} = {value}")
        else:
            source = (
                TestGraphSource(settings.repository_url)
                if settings.test_repository
                else NuGetSource(settings.repository_url)
            )
            if options.stage == 2:
                dependencies = source.direct_dependencies(
                    settings.package_name
                )
                print(f"Direct dependencies of {settings.package_name}:")
                print("\\n".join(dependencies) or "(no dependencies)")
            else:
                graph = build_graph(
                    settings.package_name,
                    source.direct_dependencies,
                    settings.filter_substring,
                )
                for package, dependencies in graph.edges.items():
                    if dependencies:
                        for dependency in dependencies:
                            print(f"{package} -> {dependency}")
                    else:
                        print(f"{package} -> (no dependencies)")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0
