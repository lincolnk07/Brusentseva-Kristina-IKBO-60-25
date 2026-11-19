"""Command-line interface for the five project stages."""

import argparse
import sys

from dependency_visualizer.config import Settings, load_settings
from dependency_visualizer.graph import ascii_tree, build_graph
from dependency_visualizer.render import save_plantuml, save_svg
from dependency_visualizer.source import NuGetSource, TestGraphSource


def parse_arguments(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for configuration and selected stage."""
    parser = argparse.ArgumentParser(
        description="Visualize dependencies of a NuGet package."
    )
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--stage", type=int, choices=range(1, 6), default=5)
    return parser.parse_args(arguments)


def create_source(settings: Settings) -> NuGetSource | TestGraphSource:
    """Create a NuGet or local test-graph source from user settings."""
    if settings.test_repository:
        return TestGraphSource(settings.repository_url)
    return NuGetSource(settings.repository_url)


def run_stage(settings: Settings, stage: int) -> None:
    """Run the requested assignment stage."""
    if stage == 1:
        print_settings(settings)
        return

    source = create_source(settings)
    if stage == 2:
        print_direct_dependencies(settings, source)
        return

    graph = build_graph(
        settings.package_name,
        source.direct_dependencies,
        settings.filter_substring,
    )
    report_cycles(graph.cycles)
    if stage == 3:
        print_graph(graph)
    elif stage == 4:
        if graph.cycles:
            print("No dependency load order exists for a cyclic graph.")
            return
        dependencies = [
            package for package in graph.load_order
            if package != graph.root
        ]
        print_load_order(dependencies)
    else:
        print_visualization(settings, graph)


def print_settings(settings: Settings) -> None:
    """Print every user-configurable parameter as key-value pairs."""
    for key, value in settings.__dict__.items():
        print(f"{key} = {value}")


def print_direct_dependencies(
    settings: Settings, source: NuGetSource | TestGraphSource
) -> None:
    """Print the direct dependencies of the configured package."""
    dependencies = source.direct_dependencies(settings.package_name)
    print(f"Direct dependencies of {settings.package_name}:")
    print_names(dependencies)


def print_graph(graph: object) -> None:
    """Print graph edges in package-to-dependency form."""
    print(f"Dependency graph for {graph.root}:")
    for package, dependencies in graph.edges.items():
        if not dependencies:
            print(f"{package} -> (no dependencies)")
        for dependency in dependencies:
            print(f"{package} -> {dependency}")


def print_load_order(packages: list[str]) -> None:
    """Print the DFS postorder used as dependency load order."""
    print("Dependency load order:")
    for index, package in enumerate(packages, start=1):
        print(f"{index}. {package}")


def print_visualization(settings: Settings, graph: object) -> None:
    """Write PlantUML and SVG files and optionally print an ASCII tree."""
    plantuml_path = save_plantuml(graph, settings.graph_file)
    svg_path = save_svg(graph, settings.graph_file)
    print(f"PlantUML source: {plantuml_path}")
    print(f"SVG image: {svg_path}")
    if settings.ascii_tree:
        print(ascii_tree(graph))


def report_cycles(cycles: list[tuple[str, str]]) -> None:
    """Report each cycle edge retained in the dependency graph."""
    for package, dependency in cycles:
        print(f"Cycle detected: {package} -> {dependency}", file=sys.stderr)


def print_names(names: list[str]) -> None:
    """Print package names or an explicit empty result."""
    if names:
        for name in names:
            print(name)
    else:
        print("(no dependencies)")


def main(arguments: list[str] | None = None) -> int:
    """Load configuration and run the selected project stage."""
    options = parse_arguments(arguments)
    try:
        settings = load_settings(options.config)
        run_stage(settings, options.stage)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0
