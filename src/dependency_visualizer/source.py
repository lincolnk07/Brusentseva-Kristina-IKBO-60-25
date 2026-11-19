"""Read direct dependencies from NuGet V3 or a TOML test graph."""

from functools import cmp_to_key
import io
import json
from pathlib import Path
import re
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as element_tree
from zipfile import ZipFile


USER_AGENT = "dependency-visualizer/1.0"
TIMEOUT_SECONDS = 20


class NuGetSource:
    """Query NuGet V3 metadata without using a package manager."""

    def __init__(self, service_index_url: str) -> None:
        """Store the service index URL and initialize request caches."""
        self.service_index_url = service_index_url
        self.package_base_url = self._find_package_base_url()
        self.version_cache: dict[str, list[str]] = {}
        self.dependency_cache: dict[str, list[str]] = {}

    def direct_dependencies(self, package_name: str) -> list[str]:
        """Return dependencies of the latest stable package version."""
        package_id = package_name.lower()
        version = self._latest_version(package_id)
        return self._dependencies_for_version(package_id, version)

    def _find_package_base_url(self) -> str:
        """Read the package base address from the NuGet service index."""
        data = self._get_json(self.service_index_url)
        resources = data.get("resources", [])
        for resource in resources:
            resource_type = resource.get("@type", "")
            if "PackageBaseAddress" in resource_type:
                return resource["@id"].rstrip("/") + "/"
        raise ValueError("NuGet service index has no PackageBaseAddress")

    def _latest_version(self, package_id: str) -> str:
        """Select the greatest stable version published by the source."""
        versions = self.version_cache.get(package_id)
        if versions is None:
            url = urljoin(self.package_base_url, f"{package_id}/index.json")
            response = self._get_json(url)
            versions = response.get("versions", [])
            self.version_cache[package_id] = versions
        stable_versions = [value for value in versions if "-" not in value]
        if not stable_versions:
            raise ValueError(f"No stable versions found for {package_id}")
        return max(stable_versions, key=cmp_to_key(compare_versions))

    def _dependencies_for_version(
        self, package_id: str, version: str
    ) -> list[str]:
        """Read and resolve all declared dependency groups in a nuspec."""
        cache_key = f"{package_id}/{version}"
        if cache_key not in self.dependency_cache:
            package_url = urljoin(
                self.package_base_url,
                f"{package_id}/{version}/{package_id}.{version}.nupkg",
            )
            package_data = self._get_bytes(package_url)
            xml_data = nuspec_from_archive(package_data)
            self.dependency_cache[cache_key] = self._parse_nuspec(xml_data)
        return self.dependency_cache[cache_key]

    def _parse_nuspec(self, xml_data: str) -> list[str]:
        """Return distinct package IDs declared in every dependency group."""
        try:
            root = element_tree.fromstring(xml_data)
        except element_tree.ParseError as error:
            raise ValueError(f"Invalid NuGet nuspec XML: {error}") from error
        dependencies = set()
        for node in root.iter():
            if node.tag.endswith("dependency"):
                dependency_id = node.attrib.get("id")
                if dependency_id:
                    dependencies.add(dependency_id)
        return sorted(dependencies, key=str.casefold)

    def _get_json(self, url: str) -> dict:
        """Fetch and decode a JSON document from the NuGet source."""
        body = self._get_text(url)
        try:
            return json.loads(body)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON from {url}: {error}") from error

    @staticmethod
    def _get_text(url: str) -> str:
        """Fetch a URL with a bounded timeout and clear error messages."""
        return NuGetSource._get_bytes(url).decode("utf-8")

    @staticmethod
    def _get_bytes(url: str) -> bytes:
        """Fetch bytes from a URL with a bounded timeout."""
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            raise ValueError(f"Cannot retrieve {url}: {error}") from error


class TestGraphSource:
    """Read a package graph from a TOML test repository file."""

    def __init__(self, path: str) -> None:
        """Load package-to-dependency mappings from a TOML file."""
        try:
            with Path(path).open("rb") as file_handle:
                values = tomllib.load(file_handle)
        except (OSError, tomllib.TOMLDecodeError) as error:
            message = f"Cannot read test repository: {error}"
            raise ValueError(message) from error
        packages = values.get("packages")
        if not isinstance(packages, dict):
            raise ValueError(
                "Test repository must define a [packages] table"
            )
        self.packages: dict[str, list[str]] = {}
        for package, dependencies in packages.items():
            self._add_package(package, dependencies)
        self._validate_dependencies()

    def direct_dependencies(self, package_name: str) -> list[str]:
        """Return dependencies declared for one package."""
        if package_name not in self.packages:
            message = f"Package {package_name!r} is absent from test graph"
            raise ValueError(message)
        return self.packages[package_name]

    def _add_package(self, package: str, dependencies: object) -> None:
        """Validate and store a single package entry."""
        if not re.fullmatch(r"[A-Z]+", package):
            message = "Test package names must be uppercase Latin letters"
            raise ValueError(message)
        if not isinstance(dependencies, list) or any(
            not isinstance(value, str) for value in dependencies
        ):
            message = f"Dependencies for {package} must be a string list"
            raise ValueError(message)
        self.packages[package] = dependencies

    def _validate_dependencies(self) -> None:
        """Require each referenced package to exist in the graph."""
        for package, dependencies in self.packages.items():
            for dependency in dependencies:
                if dependency not in self.packages:
                    message = (
                        f"Unknown dependency {dependency!r} "
                        f"referenced by {package}"
                    )
                    raise ValueError(message)


def compare_versions(first: str, second: str) -> int:
    """Compare the numeric components of NuGet stable versions."""
    first_numbers = version_numbers(first)
    second_numbers = version_numbers(second)
    width = max(len(first_numbers), len(second_numbers))
    first_numbers.extend([0] * (width - len(first_numbers)))
    second_numbers.extend([0] * (width - len(second_numbers)))
    return (first_numbers > second_numbers) - (first_numbers < second_numbers)


def version_numbers(version: str) -> list[int]:
    """Extract numeric version components, ignoring build metadata."""
    normalized = version.split("+", maxsplit=1)[0].lstrip("vV")
    if not re.fullmatch(r"\d+(\.\d+)*", normalized):
        raise ValueError(
            f"Unsupported NuGet version: {version}"
        )
    return [int(part) for part in normalized.split(".")]


def nuspec_from_archive(package_data: bytes) -> str:
    """Extract the nuspec metadata file from a NuGet package archive."""
    try:
        with ZipFile(io.BytesIO(package_data)) as archive:
            nuspec_path = next(
                name
                for name in archive.namelist()
                if name.lower().endswith(".nuspec")
            )
            return archive.read(nuspec_path).decode("utf-8-sig")
    except (OSError, StopIteration, KeyError) as error:
        message = f"NuGet package has no readable nuspec: {error}"
        raise ValueError(message) from error
