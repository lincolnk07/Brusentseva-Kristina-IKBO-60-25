"""Command-line interface through dependency load-order reporting."""

import argparse
import sys

from dependency_visualizer.config import load_settings
from dependency_visualizer.graph import build_graph
from dependency_visualizer.source import NuGetSource, TestGraphSource


def main(arguments: list[str] | None = None) -> int:
    """Run one of the first four stages."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--stage", type=int, choices=(1, 2, 3, 4), default=4)
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
                if options.stage == 3:
                    for package, dependencies in graph.edges.items():
                        if dependencies:
                            for dependency in dependencies:
                                print(f"{package} -> {dependency}")
                        else:
                            print(f"{package} -> (no dependencies)")
                elif graph.cycles:
                    for package, dependency in graph.cycles:
                        print(
                            f"Cycle detected: {package} -> {dependency}",
                            file=sys.stderr,
                        )
                    print("No dependency load order exists.")
                else:
                    print("Dependency load order:")
                    for index, package in enumerate(
                        graph.load_order[:-1], start=1
                    ):
                        print(f"{index}. {package}")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0
