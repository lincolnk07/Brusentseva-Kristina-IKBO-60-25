"""Command-line interface for dependency collection."""

import argparse
import sys

from dependency_visualizer.config import load_settings
from dependency_visualizer.source import NuGetSource


def main(arguments: list[str] | None = None) -> int:
    """Run configuration output or print direct NuGet dependencies."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--stage", type=int, choices=(1, 2), default=2)
    options = parser.parse_args(arguments)
    try:
        settings = load_settings(options.config)
        if options.stage == 1:
            for key, value in settings.__dict__.items():
                print(f"{key} = {value}")
        else:
            source = NuGetSource(settings.repository_url)
            dependencies = source.direct_dependencies(settings.package_name)
            print(f"Direct dependencies of {settings.package_name}:")
            if dependencies:
                print("\\n".join(dependencies))
            else:
                print("(no dependencies)")
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0
