"""Mocked HTTP tests for NuGet V3 metadata and package downloads."""

from io import BytesIO
import json
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from zipfile import ZipFile

from dependency_visualizer.source import NuGetSource


SERVICE_URL = "https://api.example.test/v3/index.json"
BASE_URL = "https://api.example.test/v3-flatcontainer/"


class FakeResponse:
    """Small context-managed response compatible with urllib.urlopen."""

    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


def service_index() -> bytes:
    """Serialize a service index containing a package base address."""
    return json.dumps(
        {
            "resources": [
                {
                    "@type": "PackageBaseAddress/3.0.0",
                    "@id": BASE_URL,
                }
            ]
        }
    ).encode("utf-8")


def package_archive(nuspec: str) -> bytes:
    """Create an in-memory NuGet archive with one nuspec file."""
    archive_data = BytesIO()
    with ZipFile(archive_data, "w") as archive:
        archive.writestr("Alpha.nuspec", nuspec)
    return archive_data.getvalue()


def latest_version_response() -> tuple[object, list[tuple[str, int]]]:
    """Prepare mocked NuGet responses for latest-version selection."""
    nuspec = (
        '<package><metadata><dependencies>'
        '<group targetFramework="net8.0">'
        '<dependency id="Shared" version="[1.0.0, 2.0.0)"/>'
        '<dependency id="Modern" version="[4.0, 5.0)"/>'
        '</group>'
        '<group targetFramework=".NETFramework4.7.2">'
        '<dependency id="Shared" version="[3.0.0, 4.0.0)"/>'
        '<dependency id="Legacy" version="2.0"/>'
        '</group>'
        '</dependencies></metadata></package>'
    )
    package_bytes = package_archive(nuspec)
    requested_urls: list[tuple[str, int]] = []

    def open_url(request: object, timeout: int) -> FakeResponse:
        url = request.full_url
        requested_urls.append((url, timeout))
        if url == SERVICE_URL:
            return FakeResponse(service_index())
        if url == f"{BASE_URL}alpha/index.json":
            versions = {"versions": ["1.0.0", "1.2.0", "2.0.0-rc.1"]}
            return FakeResponse(json.dumps(versions).encode("utf-8"))
        if url == f"{BASE_URL}alpha/1.2.0/alpha.1.2.0.nupkg":
            return FakeResponse(package_bytes)
        raise AssertionError(f"Unexpected HTTP URL: {url}")

    return open_url, requested_urls


class NuGetHttpTests(unittest.TestCase):
    """Verify V3 source selection, downloads, and API failures."""

    def test_reads_service_index_and_latest_version_groups(self) -> None:
        """Choose latest stable and merge declared framework groups."""
        open_url, requested_urls = latest_version_response()
        with patch(
            "dependency_visualizer.source.urlopen", side_effect=open_url
        ):
            source = NuGetSource(SERVICE_URL)
            dependencies = source.direct_dependencies("Alpha")

        self.assertEqual(dependencies, ["Legacy", "Modern", "Shared"])
        self.assertEqual(requested_urls[-1][1], 20)
        self.assertTrue(
            any(url.endswith("/alpha/index.json") for url, _ in requested_urls)
        )
        self.assertFalse(
            any("2.0.0-rc.1" in url for url, _ in requested_urls)
        )

    def test_parent_range_does_not_select_transitive_version(self) -> None:
        """Expose why NuGet restore can differ from this generalized graph."""
        alpha_nuspec = (
            '<package><metadata><dependencies>'
            '<dependency id="Beta" version="[1.0.0, 2.0.0)"/>'
            '</dependencies></metadata></package>'
        )
        empty_nuspec = "<package><metadata/></package>"
        requested_urls = []

        def open_url(request: object, timeout: int) -> FakeResponse:
            url = request.full_url
            self.assertEqual(timeout, 20)
            requested_urls.append(url)
            if url == SERVICE_URL:
                return FakeResponse(service_index())
            if url == f"{BASE_URL}alpha/index.json":
                return FakeResponse(b'{"versions": ["1.0.0"]}')
            if url == f"{BASE_URL}beta/index.json":
                return FakeResponse(
                    b'{"versions": ["1.5.0", "3.0.0"]}'
                )
            if url == f"{BASE_URL}alpha/1.0.0/alpha.1.0.0.nupkg":
                return FakeResponse(package_archive(alpha_nuspec))
            if url == f"{BASE_URL}beta/3.0.0/beta.3.0.0.nupkg":
                return FakeResponse(package_archive(empty_nuspec))
            self.fail(f"Unexpected HTTP URL: {url}")

        with patch(
            "dependency_visualizer.source.urlopen", side_effect=open_url
        ):
            source = NuGetSource(SERVICE_URL)
            self.assertEqual(source.direct_dependencies("Alpha"), ["Beta"])
            source.direct_dependencies("Beta")

        self.assertIn(
            f"{BASE_URL}beta/3.0.0/beta.3.0.0.nupkg", requested_urls
        )

    def test_rejects_service_index_without_package_base_address(self) -> None:
        """Report a service index that lacks the V3 flat-container resource."""
        body = json.dumps({"resources": []}).encode("utf-8")
        with patch(
            "dependency_visualizer.source.urlopen",
            return_value=FakeResponse(body),
        ):
            with self.assertRaisesRegex(
                ValueError, "no PackageBaseAddress"
            ):
                NuGetSource(SERVICE_URL)

    def test_reports_http_404_and_500(self) -> None:
        """Turn HTTP status errors into clear source exceptions."""
        for status in (404, 500):
            with self.subTest(status=status):
                error = HTTPError(
                    SERVICE_URL, status, "HTTP failure", None, None
                )
                with patch(
                    "dependency_visualizer.source.urlopen",
                    side_effect=error,
                ):
                    with self.assertRaisesRegex(
                        ValueError, "Cannot retrieve"
                    ):
                        NuGetSource(SERVICE_URL)

    def test_rejects_malformed_service_index_json(self) -> None:
        """Report malformed JSON returned by the service index."""
        with patch(
            "dependency_visualizer.source.urlopen",
            return_value=FakeResponse(b"{broken"),
        ):
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                NuGetSource(SERVICE_URL)

    def test_reports_missing_package_as_http_404(self) -> None:
        """Report a missing package when its versions endpoint returns 404."""
        error = HTTPError(
            f"{BASE_URL}missing/index.json",
            404,
            "Not Found",
            None,
            None,
        )
        with patch(
            "dependency_visualizer.source.urlopen",
            side_effect=[FakeResponse(service_index()), error],
        ):
            source = NuGetSource(SERVICE_URL)
            with self.assertRaisesRegex(ValueError, "Cannot retrieve"):
                source.direct_dependencies("Missing")

    def test_reports_package_without_stable_versions(self) -> None:
        """Reject an empty version index or prerelease-only package."""
        version_index = {"versions": ["1.0.0-beta.1"]}
        with patch(
            "dependency_visualizer.source.urlopen",
            side_effect=[
                FakeResponse(service_index()),
                FakeResponse(json.dumps(version_index).encode("utf-8")),
            ],
        ):
            source = NuGetSource(SERVICE_URL)
            with self.assertRaisesRegex(ValueError, "No stable versions"):
                source.direct_dependencies("Alpha")

    def test_reports_corrupt_nupkg_archive(self) -> None:
        """Convert an invalid zip package into a clear ValueError."""
        version_index = {"versions": ["1.0.0"]}
        with patch(
            "dependency_visualizer.source.urlopen",
            side_effect=[
                FakeResponse(service_index()),
                FakeResponse(json.dumps(version_index).encode("utf-8")),
                FakeResponse(b"not a zip archive"),
            ],
        ):
            source = NuGetSource(SERVICE_URL)
            with self.assertRaisesRegex(
                ValueError, "no readable nuspec"
            ):
                source.direct_dependencies("Alpha")


if __name__ == "__main__":
    unittest.main()
