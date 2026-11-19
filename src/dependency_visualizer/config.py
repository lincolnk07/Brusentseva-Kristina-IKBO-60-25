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
    """Validate field types and the active repository location."""
    if not isinstance(settings.package_name, str) or not settings.package_name:
        raise ValueError("package_name must be a non-empty string")
    if (
        not isinstance(settings.repository_url, str)
        or not settings.repository_url
    ):
        raise ValueError("repository_url must be a non-empty string")
    if not isinstance(settings.test_repository, bool):
        raise ValueError("test_repository must be true or false")
    if not isinstance(settings.graph_file, str) or not settings.graph_file:
        raise ValueError("graph_file must be a non-empty file name")
    if Path(settings.graph_file).suffix.lower() != ".svg":
        raise ValueError("graph_file must have the .svg extension")
    if not isinstance(settings.ascii_tree, bool):
        raise ValueError("ascii_tree must be true or false")
    if not isinstance(settings.filter_substring, str):
        raise ValueError("filter_substring must be a string")

    if settings.test_repository:
        if not Path(settings.repository_url).is_file():
            raise ValueError("Test repository file does not exist")
    else:
        parsed_url = urlparse(settings.repository_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(
                "repository_url must be an HTTP or HTTPS URL"
            )
