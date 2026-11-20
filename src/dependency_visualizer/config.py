"""Configuration loading and validation."""

from dataclasses import dataclass
from pathlib import Path
import tomllib
from urllib.parse import urlparse


@dataclass(frozen=True)
class Settings:
    """User-configurable parameters required by the assignment."""

    package_name: str
    repository_url: str
    test_repository: bool
    graph_file: str
    ascii_tree: bool
    filter_substring: str


CONFIG_KEYS = {
    "package_name",
    "repository_url",
    "test_repository",
    "graph_file",
    "ascii_tree",
    "filter_substring",
}


def load_settings(path: str) -> Settings:
    """Load a TOML configuration file and validate all parameters."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ValueError(f"Configuration file does not exist: {path}")

    try:
        with config_path.open("rb") as file_handle:
            values = tomllib.load(file_handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Cannot read TOML configuration: {error}") from error

    extra_keys = set(values) - CONFIG_KEYS
    missing_keys = CONFIG_KEYS - set(values)
    if extra_keys or missing_keys:
        details = []
        if missing_keys:
            details.append(f"missing: {', '.join(sorted(missing_keys))}")
        if extra_keys:
            details.append(f"unknown: {', '.join(sorted(extra_keys))}")
        message = "; ".join(details)
        raise ValueError(f"Invalid configuration keys ({message})")

    settings = Settings(**values)
    validate_settings(settings)
    return settings


def validate_settings(settings: Settings) -> None:
    """Validate all configuration parameters."""
    validate_package_name(settings.package_name)
    validate_boolean(settings.test_repository, "test_repository")
    validate_repository_url(
        settings.repository_url,
        settings.test_repository,
    )
    validate_graph_file(settings.graph_file)
    validate_boolean(settings.ascii_tree, "ascii_tree")
    validate_filter_substring(settings.filter_substring)


def validate_package_name(package_name: str) -> None:
    """Validate the package name."""
    if not isinstance(package_name, str) or not package_name:
        raise ValueError("package_name must be a non-empty string")


def validate_repository_url(
    repository_url: str,
    test_repository: bool,
) -> None:
    """Validate the repository URL or test repository path."""
    if not isinstance(repository_url, str) or not repository_url:
        raise ValueError("repository_url must be a non-empty string")

    if test_repository:
        if not Path(repository_url).is_file():
            raise ValueError("Test repository file does not exist")
    else:
        parsed_url = urlparse(repository_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(
                "repository_url must be an HTTP or HTTPS URL"
            )


def validate_boolean(value: object, name: str) -> None:
    """Validate a boolean configuration parameter."""
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be true or false")


def validate_graph_file(graph_file: str) -> None:
    """Validate the output SVG file name."""
    if not isinstance(graph_file, str) or not graph_file:
        raise ValueError("graph_file must be a non-empty file name")

    if Path(graph_file).suffix.lower() != ".svg":
        raise ValueError("graph_file must have the .svg extension")


def validate_filter_substring(filter_substring: str) -> None:
    """Validate the dependency filter."""
    if not isinstance(filter_substring, str):
        raise ValueError("filter_substring must be a string")
