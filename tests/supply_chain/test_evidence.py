"""Tests for normalized SBOM, scan, and retained evidence behavior."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tools.supply_chain.evidence import (
    FIXED_CREATED,
    docker_archive_config_id,
    finalize_bundle,
    normalize_database_status,
    normalize_image_metadata,
    normalize_scan,
    normalize_spdx,
    normalize_syft_sbom,
    package_signature,
    rootfs_manifest,
    sha256_file,
    validate_bundle,
    validate_database_status,
)
from tools.supply_chain.policy import (
    POLICY_PATH,
    ROOT,
    PolicyError,
    load_json,
    write_json,
)


def spdx_package(name: str, index: int) -> dict[str, object]:
    return {
        "SPDXID": f"SPDXRef-Package-{index}",
        "downloadLocation": "NOASSERTION",
        "externalRefs": [
            {
                "referenceCategory": "PACKAGE-MANAGER",
                "referenceLocator": f"pkg:generic/{name}@1.0.0",
                "referenceType": "purl",
            }
        ],
        "filesAnalyzed": False,
        "licenseConcluded": "NOASSERTION",
        "licenseDeclared": "NOASSERTION",
        "name": name,
        "versionInfo": "1.0.0",
    }


class EvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.policy = load_json(POLICY_PATH)
        for directory in ("images", "sboms", "scan-sboms", "scans", "scanner"):
            (self.root / directory).mkdir(parents=True)

    def metadata(self, image: str) -> dict[str, object]:
        labels = {}
        if image != "postgres":
            labels = {
                "org.opencontainers.image.created": FIXED_CREATED,
                "org.opencontainers.image.description": "Test image",
                "org.opencontainers.image.licenses": "Apache-2.0",
                "org.opencontainers.image.revision": "local",
                "org.opencontainers.image.source": (
                    "https://github.com/ulfe-lmi/slaif-agent-site"
                ),
                "org.opencontainers.image.title": image,
                "org.opencontainers.image.version": "0.0.0",
            }
        return {
            "architecture": "amd64",
            "created": FIXED_CREATED,
            "image_id": "sha256:" + "a" * 64,
            "labels": labels,
            "os": "linux",
            "repo_digests": [],
            "schema_version": 1,
        }

    def populate(self, critical: bool = False) -> None:
        status = {
            "built": datetime.now(UTC).isoformat(),
            "checksum": "sha256:" + "b" * 64,
        }
        write_json(self.root / "scanner/grype-database.json", status)
        for image, configured in self.policy["required_images"].items():
            write_json(self.root / f"images/{image}.json", self.metadata(image))
            packages = [
                spdx_package(name, index)
                for index, name in enumerate(configured["expected_components"], 1)
            ]
            write_json(
                self.root / f"sboms/{image}.spdx.json",
                {
                    "dataLicense": "CC0-1.0",
                    "documentNamespace": f"https://example.invalid/{image}",
                    "name": image,
                    "packages": packages,
                    "relationships": [
                        {
                            "relatedSpdxElement": packages[0]["SPDXID"],
                            "relationshipType": "DESCRIBES",
                            "spdxElementId": "SPDXRef-DOCUMENT",
                        }
                    ],
                    "SPDXID": "SPDXRef-DOCUMENT",
                    "spdxVersion": "SPDX-2.3",
                },
            )
            scan_sbom_path = self.root / f"scan-sboms/{image}.syft.json"
            write_json(
                scan_sbom_path,
                {"slaifEvidence": {"image_id": "sha256:" + "a" * 64}},
            )
            matches: list[dict[str, object]] = []
            if image == "browser-worker":
                for exception in load_json(
                    ROOT / "supply-chain/vulnerability-exceptions.json"
                )["exceptions"]:
                    matches.append(
                        {
                            "artifact": {
                                "name": "chrome",
                                "purl": exception["affected"],
                                "version": "152.0.7977.64",
                            },
                            "vulnerability": {
                                "id": exception["identifier"],
                                "severity": "Critical",
                            },
                        }
                    )
            if critical and image == "backend":
                matches.append(
                    {
                        "artifact": {
                            "name": "example",
                            "purl": "pkg:pypi/example@1.0.0",
                            "version": "1.0.0",
                        },
                        "vulnerability": {
                            "id": "CVE-2026-9999",
                            "severity": "Critical",
                        },
                    }
                )
            write_json(
                self.root / f"scans/{image}.grype.json",
                {
                    "descriptor": {},
                    "matches": matches,
                    "source": {},
                    "slaifEvidence": {
                        "image": image,
                        "sbom_sha256": sha256_file(scan_sbom_path),
                    },
                },
            )

    def test_spdx_and_image_metadata_normalization(self) -> None:
        document = {
            "creationInfo": {
                "created": "2026-08-17T00:00:00Z",
                "creators": ["Tool: syft-1.51.0"],
            },
            "dataLicense": "CC0-1.0",
            "packages": [spdx_package("example", 1)],
            "relationships": [
                {
                    "relatedSpdxElement": "SPDXRef-Package-1",
                    "relationshipType": "DESCRIBES",
                    "spdxElementId": "SPDXRef-DOCUMENT",
                }
            ],
            "SPDXID": "SPDXRef-DOCUMENT",
            "spdxVersion": "SPDX-2.3",
        }
        normalized = normalize_spdx(document, "backend", "sha256:" + "a" * 64, "local")
        self.assertEqual(normalized["creationInfo"]["created"], FIXED_CREATED)
        self.assertIn("image_id=sha256:", normalized["annotations"][0]["comment"])

        raw_metadata = {
            "_list": [
                {
                    "Architecture": "amd64",
                    "Config": {"Labels": {"example": "value"}},
                    "Created": FIXED_CREATED,
                    "Id": "sha256:" + "c" * 64,
                    "Os": "linux",
                    "RepoDigests": ["example@sha256:" + "d" * 64],
                }
            ]
        }
        metadata = normalize_image_metadata(raw_metadata)
        self.assertEqual(metadata["labels"], {"example": "value"})

    def test_scan_normalization_rejects_malformed_result(self) -> None:
        with self.assertRaisesRegex(PolicyError, "malformed Grype JSON"):
            normalize_scan({"descriptor": {}}, "backend", "a" * 64)

    def test_symbol_aware_syft_scan_sbom_is_normalized(self) -> None:
        image_id = "sha256:" + "a" * 64
        archive_config_id = "sha256:" + "b" * 64
        document = {
            "artifacts": [
                {"id": "b", "name": "z", "type": "apk", "version": "1"},
                {"id": "a", "name": "a", "type": "apk", "version": "1"},
            ],
            "artifactRelationships": [],
            "descriptor": {"name": "syft", "version": "1.51.0"},
            "files": [],
            "schema": {"version": "16.1.10"},
            "source": {
                "name": "/scan/image.tar",
                "metadata": {
                    "imageID": archive_config_id,
                    "userInput": "/scan/image.tar",
                },
            },
        }
        normalized = normalize_syft_sbom(
            document, "backend", image_id, archive_config_id, "local"
        )
        self.assertEqual(normalized["artifacts"][0]["name"], "a")
        self.assertEqual(normalized["slaifEvidence"]["go_symbol_capture"], "stdlib")
        self.assertEqual(
            normalized["slaifEvidence"]["archive_config_id"], archive_config_id
        )
        self.assertEqual(normalized["source"]["metadata"]["userInput"], "image:backend")

    def test_docker_archive_config_identity_is_content_verified(self) -> None:
        config = b'{"architecture":"amd64","os":"linux"}'
        digest = hashlib.sha256(config).hexdigest()
        archive = self.root / "image.tar"
        manifest = json.dumps(
            [{"Config": f"blobs/sha256/{digest}", "RepoTags": ["example:local"]}]
        ).encode()
        with tarfile.open(archive, "w") as bundle:
            for name, content in (
                ("manifest.json", manifest),
                (f"blobs/sha256/{digest}", config),
            ):
                metadata = tarfile.TarInfo(name)
                metadata.size = len(content)
                bundle.addfile(metadata, io.BytesIO(content))
        self.assertEqual(docker_archive_config_id(archive), f"sha256:{digest}")

        with tarfile.open(archive, "w") as bundle:
            invalid_name = "blobs/sha256/" + "a" * 64
            invalid_manifest = json.dumps([{"Config": invalid_name}]).encode()
            for name, content in (
                ("manifest.json", invalid_manifest),
                (invalid_name, config),
            ):
                metadata = tarfile.TarInfo(name)
                metadata.size = len(content)
                bundle.addfile(metadata, io.BytesIO(content))
        with self.assertRaisesRegex(PolicyError, "config checksum mismatch"):
            docker_archive_config_id(archive)

    def test_package_signature_excludes_only_syft_archive_wrapper(self) -> None:
        package = spdx_package("example", 1)
        wrapper = spdx_package("/scan/image.tar", 2)
        wrapper.update(
            {
                "SPDXID": "SPDXRef-DocumentRoot-Image--scan-image.tar",
                "primaryPackagePurpose": "CONTAINER",
                "versionInfo": "sha256:" + "a" * 64,
            }
        )
        document = {"packages": [package, wrapper]}
        self.assertEqual(
            package_signature(document),
            package_signature({"packages": [package]}),
        )

        wrapper["SPDXID"] = "SPDXRef-Package-real-container"
        self.assertEqual(len(package_signature(document)), 2)

    def test_stale_database_fails(self) -> None:
        stale = {
            "built": (datetime.now(UTC) - timedelta(days=8)).isoformat(),
            "checksum": "sha256:" + "a" * 64,
        }
        with self.assertRaisesRegex(PolicyError, "exceeds"):
            validate_database_status(stale, 120)

    def test_database_status_extracts_official_source_checksum(self) -> None:
        checksum = "a" * 64
        normalized = normalize_database_status(
            {
                "schemaVersion": "v6.1.9",
                "from": (
                    "https://grype.anchore.io/databases/v6/database.tar.zst"
                    f"?checksum=sha256%3A{checksum}"
                ),
                "built": datetime.now(UTC).isoformat(),
                "valid": True,
            }
        )
        self.assertEqual(normalized["checksum"], f"sha256:{checksum}")

    def test_finalize_checksum_tamper_and_secret_leakage(self) -> None:
        self.populate()
        (self.root / "artifact.bin").write_bytes(b"\xff\xfe\x00binary")
        index = finalize_bundle(self.root, "local")
        self.assertEqual(len(index["images"]), 6)
        validate_bundle(self.root)
        (self.root / "SUMMARY.txt").write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(PolicyError, "tampered"):
            validate_bundle(self.root)

        self.populate()
        (self.root / "leak.bin").write_bytes(
            b"\xff\xfe\x00-----BEGIN PRIVATE KEY-----\n"
        )
        with self.assertRaisesRegex(PolicyError, "forbidden evidence marker"):
            finalize_bundle(self.root, "local")

    def test_exception_set_is_retained_and_synthetic_thirty_second_finding_fails(
        self,
    ) -> None:
        self.populate()
        index = finalize_bundle(self.root, "local")
        browser = next(
            image for image in index["images"] if image["image"] == "browser-worker"
        )
        self.assertEqual(len(browser["critical_findings"]), 31)
        self.assertEqual(
            index["exception_counts"]["vulnerability"],
            31,
        )
        self.assertEqual(
            {item["status"] for item in browser["critical_findings"]},
            {"excepted"},
        )

        scan_path = self.root / "scans/browser-worker.grype.json"
        scan = load_json(scan_path)
        scan["matches"].append(
            {
                "artifact": {
                    "name": "chrome",
                    "purl": "pkg:generic/chrome@152.0.7977.64",
                    "version": "152.0.7977.64",
                },
                "vulnerability": {
                    "id": "CVE-2026-79999",
                    "severity": "Critical",
                },
            }
        )
        write_json(scan_path, scan)
        with self.assertRaisesRegex(PolicyError, "unexcepted Critical"):
            finalize_bundle(self.root, "local")

    def test_critical_and_missing_image_fail_closed(self) -> None:
        self.populate(critical=True)
        with self.assertRaisesRegex(PolicyError, "unexcepted Critical"):
            finalize_bundle(self.root, "local")

        self.populate()
        (self.root / "sboms/web.spdx.json").unlink()
        with self.assertRaisesRegex(PolicyError, "invalid JSON"):
            finalize_bundle(self.root, "local")

    def test_rootfs_manifest_is_normalized_and_bounded(self) -> None:
        archive = self.root / "rootfs.tar"
        with tarfile.open(archive, "w") as stream:
            data = b"application"
            included = tarfile.TarInfo("opt/slaif/app.py")
            included.mode = 0o440
            included.size = len(data)
            stream.addfile(included, io.BytesIO(data))
            excluded = tarfile.TarInfo("etc/hostname")
            excluded.size = 4
            stream.addfile(excluded, io.BytesIO(b"host"))
        manifest = rootfs_manifest(archive, "backend")
        self.assertEqual(len(manifest["entries"]), 1)
        self.assertEqual(manifest["entries"][0]["path"], "opt/slaif/app.py")

    def test_web_rootfs_normalizes_only_named_next_cryptographic_fields(self) -> None:
        manifests = []
        for index, marker in enumerate(("a", "b")):
            archive = self.root / f"web-{index}.tar"
            with tarfile.open(archive, "w") as stream:
                documents = {
                    "opt/slaif/apps/web/.next/prerender-manifest.json": {
                        "routes": {"/": {"htmlSize": 12}},
                        "preview": {
                            "previewModeId": marker * 32,
                            "previewModeSigningKey": marker * 64,
                            "previewModeEncryptionKey": marker * 64,
                        },
                    },
                    "opt/slaif/apps/web/.next/server/server-reference-manifest.json": {
                        "node": {},
                        "edge": {},
                        "encryptionKey": marker * 44,
                    },
                    "opt/slaif/apps/web/.next/server/server-reference-manifest.js": (
                        "self.__RSC_SERVER_MANIFEST="
                        + json.dumps(
                            json.dumps(
                                {"node": {}, "edge": {}, "encryptionKey": marker * 44}
                            )
                        )
                    ),
                }
                for name, document in documents.items():
                    data = (
                        document.encode()
                        if isinstance(document, str)
                        else json.dumps(document).encode()
                    )
                    member = tarfile.TarInfo(name)
                    member.size = len(data)
                    stream.addfile(member, io.BytesIO(data))
            manifests.append(rootfs_manifest(archive, "web"))
        self.assertEqual(manifests[0], manifests[1])
        normalized = [
            entry for entry in manifests[0]["entries"] if entry["normalized_fields"]
        ]
        self.assertEqual(len(normalized), 3)

        changed = manifests[1]["entries"][0]
        changed["size"] += 1
        self.assertNotEqual(manifests[0], manifests[1])


if __name__ == "__main__":
    unittest.main()
