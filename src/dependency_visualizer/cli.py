"""Command-line interface for the configuration prototype."""

import argparse
import sys

from dependency_visualizer.config import load_settings


def main(arguments: list[str] | None = None) -> int:
    """Load configuration and print all configured parameters."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.toml")
    parser.add_argument("--stage", type=int, choices=(1,), default=1)
    options = parser.parse_args(arguments)
    try:
        settings = load_settings(options.config)
    except (OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    for key, value in settings.__dict__.items():
        print(f"{key} = {value}")
    return 0
