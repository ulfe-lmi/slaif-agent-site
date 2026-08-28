#!/usr/bin/env python3
"""Normalize, validate, and checksum local supply-chain evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import tarfile
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, BinaryIO
from urllib.parse import parse_qs, urlparse

from tools.supply_chain.policy import (
    POLICY_PATH,
    ROOT,
    VULNERABILITY_EXCEPTIONS_PATH,
    PolicyError,
    load_json,
    validate_exceptions,
    validate_policy,
    write_json,
)

FIXED_CREATED = "2024-01-01T00:00:00Z"
HEX_ID = re.compile(r"sha256:[0-9a-f]{64}")
SPDX_ID = re.compile(r"SPDXRef-[A-Za-z0-9.-]+")
IMAGE_PREFIXES = {
    "apache": ("usr/local/apache2/conf/",),
    "backend": ("opt/slaif/",),
    "browser-worker": ("opt/slaif/", "ms-playwright/chromium-1669021/"),
    "nginx": ("etc/nginx/nginx.conf",),
    "web": ("opt/slaif/",),
}
NEXT_PRERENDER_MANIFEST = "opt/slaif/apps/web/.next/prerender-manifest.json"
NEXT_SERVER_REFERENCE_JSON = (
    "opt/slaif/apps/web/.next/server/server-reference-manifest.json"
)
NEXT_SERVER_REFERENCE_JS = (
    "opt/slaif/apps/web/.next/server/server-reference-manifest.js"
)
NORMALIZED_SECRET = "<normalized-per-build-cryptographic-value>"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: str) -> dict[str, Any]:
    if path == "-":
        try:
            value = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise PolicyError(f"standard input: invalid JSON ({exc})") from exc
        if not isinstance(value, dict) and not isinstance(value, list):
            raise PolicyError("standard input: JSON must be an object or array")
        return {"_list": value} if isinstance(value, list) else value
    return load_json(Path(path))


def normalize_image_metadata(document: dict[str, Any]) -> dict[str, Any]:
    raw: object = document.get("_list", document)
    if not isinstance(raw, list) or len(raw) != 1 or not isinstance(raw[0], dict):
        raise PolicyError("docker image metadata must contain exactly one image")
    image = raw[0]
    config = image.get("Config")
    if not isinstance(config, dict):
        raise PolicyError("docker image metadata has no Config object")
    labels = config.get("Labels") or {}
    if not isinstance(labels, dict):
        raise PolicyError("docker image labels are malformed")
    image_id = image.get("Id")
    if not isinstance(image_id, str) or not HEX_ID.fullmatch(image_id):
        raise PolicyError("docker image ID is not an immutable SHA-256")
    repo_digests = image.get("RepoDigests") or []
    if not isinstance(repo_digests, list):
        raise PolicyError("docker RepoDigests is malformed")
    return {
        "architecture": image.get("Architecture"),
        "created": image.get("Created"),
        "image_id": image_id,
        "labels": {str(key): str(value) for key, value in sorted(labels.items())},
        "os": image.get("Os"),
        "repo_digests": sorted(str(item) for item in repo_digests),
        "schema_version": 1,
    }


def normalize_spdx(
    document: dict[str, Any],
    image_name: str,
    image_id: str,
    source_revision: str,
) -> dict[str, Any]:
    if document.get("spdxVersion") != "SPDX-2.3":
        raise PolicyError(f"{image_name}: Syft output is not SPDX 2.3")
    if document.get("dataLicense") != "CC0-1.0":
        raise PolicyError(f"{image_name}: SPDX data license is not CC0-1.0")
    if not HEX_ID.fullmatch(image_id):
        raise PolicyError(f"{image_name}: image ID is malformed")
    if not re.fullmatch(r"(?:local|[0-9a-f]{40})", source_revision):
        raise PolicyError(f"{image_name}: source revision is malformed")
    creation = document.get("creationInfo")
    if not isinstance(creation, dict):
        raise PolicyError(f"{image_name}: SPDX creationInfo is missing")
    creators = creation.get("creators")
    if not isinstance(creators, list) or not any(
        "syft" in str(creator).casefold() for creator in creators
    ):
        raise PolicyError(f"{image_name}: SPDX creator does not identify Syft")
    creation["created"] = FIXED_CREATED
    creation["creators"] = sorted(str(creator) for creator in creators)
    packages = document.get("packages")
    relationships = document.get("relationships")
    if not isinstance(packages, list) or not packages:
        raise PolicyError(f"{image_name}: SPDX package inventory is empty")
    if not isinstance(relationships, list) or not relationships:
        raise PolicyError(f"{image_name}: SPDX relationships are empty")
    for package in packages:
        if not isinstance(package, dict) or not SPDX_ID.fullmatch(
            str(package.get("SPDXID", ""))
        ):
            raise PolicyError(f"{image_name}: malformed SPDX package")
        if not package.get("name") or not package.get("versionInfo"):
            raise PolicyError(f"{image_name}: SPDX package identity is incomplete")
        if not package.get("licenseDeclared"):
            package["licenseDeclared"] = "NOASSERTION"
        external = package.get("externalRefs")
        if isinstance(external, list):
            package["externalRefs"] = sorted(
                external,
                key=lambda item: (
                    str(item.get("referenceCategory", "")),
                    str(item.get("referenceType", "")),
                    str(item.get("referenceLocator", "")),
                ),
            )
    document["packages"] = sorted(
        packages,
        key=lambda item: (
            str(item.get("name", "")).casefold(),
            str(item.get("versionInfo", "")),
            str(item.get("SPDXID", "")),
        ),
    )
    document["relationships"] = sorted(
        relationships,
        key=lambda item: (
            str(item.get("spdxElementId", "")),
            str(item.get("relationshipType", "")),
            str(item.get("relatedSpdxElement", "")),
        ),
    )
    files = document.get("files")
    if isinstance(files, list):
        document["files"] = sorted(
            files,
            key=lambda item: (
                str(item.get("fileName", "")),
                str(item.get("SPDXID", "")),
            ),
        )
    clean_id = image_id.removeprefix("sha256:")
    document["name"] = f"slaif-agent-site-{image_name}-{source_revision[:12]}"
    document["documentNamespace"] = (
        "https://github.com/ulfe-lmi/slaif-agent-site/sbom/"
        f"{source_revision}/{image_name}/{clean_id}"
    )
    document["annotations"] = [
        {
            "annotationDate": FIXED_CREATED,
            "annotationType": "OTHER",
            "annotator": "Tool: slaif-agent-site-supply-chain-policy",
            "comment": (
                f"image={image_name}; image_id={image_id}; "
                f"source_revision={source_revision}"
            ),
        }
    ]
    return document


def package_signature(document: dict[str, Any]) -> list[dict[str, Any]]:
    signature = []
    for package in document.get("packages", []):
        # Syft represents the scanned Docker archive itself as a synthetic
        # container package. Its version and purl are the archive digest, which
        # changes with Docker's out-of-contract OCI timestamps even when every
        # installed package and application file is identical.
        if (
            str(package.get("SPDXID", "")).startswith("SPDXRef-DocumentRoot-")
            and package.get("primaryPackagePurpose") == "CONTAINER"
        ):
            continue
        purls = sorted(
            str(reference.get("referenceLocator"))
            for reference in package.get("externalRefs", [])
            if reference.get("referenceType") == "purl"
        )
        signature.append(
            {
                "license_declared": package.get("licenseDeclared", "NOASSERTION"),
                "name": package.get("name"),
                "purls": purls,
                "version": package.get("versionInfo"),
            }
        )
    return sorted(
        signature,
        key=lambda item: (
            str(item["name"]).casefold(),
            str(item["version"]),
            item["purls"],
        ),
    )


def normalize_syft_sbom(
    document: dict[str, Any],
    image_name: str,
    image_id: str,
    archive_config_id: str,
    source_revision: str,
) -> dict[str, Any]:
    schema = document.get("schema")
    descriptor = document.get("descriptor")
    artifacts = document.get("artifacts")
    relationships = document.get("artifactRelationships")
    files = document.get("files")
    source = document.get("source")
    if not isinstance(schema, dict) or not schema.get("version"):
        raise PolicyError(f"{image_name}: Syft scan SBOM schema is missing")
    if not isinstance(descriptor, dict) or descriptor.get("name") != "syft":
        raise PolicyError(f"{image_name}: Syft scan SBOM descriptor is invalid")
    if not isinstance(artifacts, list) or not artifacts:
        raise PolicyError(f"{image_name}: Syft scan SBOM package inventory is empty")
    if not isinstance(relationships, list) or not isinstance(files, list):
        raise PolicyError(
            f"{image_name}: Syft scan SBOM relationships/files are invalid"
        )
    if not isinstance(source, dict) or not isinstance(source.get("metadata"), dict):
        raise PolicyError(f"{image_name}: Syft scan SBOM source is missing")
    if not HEX_ID.fullmatch(image_id) or not HEX_ID.fullmatch(archive_config_id):
        raise PolicyError(f"{image_name}: image identity is malformed")
    if source["metadata"].get("imageID") != archive_config_id:
        raise PolicyError(f"{image_name}: Syft scan SBOM image identity mismatch")
    if not re.fullmatch(r"(?:local|[0-9a-f]{40})", source_revision):
        raise PolicyError(f"{image_name}: source revision is malformed")
    source["name"] = image_name
    source["metadata"]["userInput"] = f"image:{image_name}"
    document["artifacts"] = sorted(
        artifacts,
        key=lambda item: (
            str(item.get("name", "")).casefold(),
            str(item.get("version", "")),
            str(item.get("type", "")),
            str(item.get("id", "")),
        ),
    )
    document["artifactRelationships"] = sorted(
        relationships,
        key=lambda item: (
            str(item.get("parent", "")),
            str(item.get("type", "")),
            str(item.get("child", "")),
        ),
    )
    document["files"] = sorted(
        files,
        key=lambda item: (
            str(item.get("location", {}).get("path", "")),
            str(item.get("id", "")),
        ),
    )
    document["slaifEvidence"] = {
        "archive_config_id": archive_config_id,
        "go_symbol_capture": "stdlib",
        "image": image_name,
        "image_id": image_id,
        "source_revision": source_revision,
    }
    return document


def docker_archive_config_id(archive: Path) -> str:
    """Return and verify the immutable config digest in a Docker image archive."""
    try:
        with tarfile.open(archive, "r:*") as bundle:
            manifest_member = bundle.getmember("manifest.json")
            manifest_stream = bundle.extractfile(manifest_member)
            if manifest_stream is None:
                raise PolicyError("docker archive manifest.json is not a file")
            manifest = json.loads(manifest_stream.read())
            if (
                not isinstance(manifest, list)
                or len(manifest) != 1
                or not isinstance(manifest[0], dict)
            ):
                raise PolicyError("docker archive must contain exactly one image")
            config_name = manifest[0].get("Config")
            match = re.fullmatch(
                r"(?:blobs/sha256/)?([0-9a-f]{64})(?:\.json)?",
                str(config_name),
            )
            if match is None:
                raise PolicyError("docker archive config path is malformed")
            config_member = bundle.getmember(str(config_name))
            config_stream = bundle.extractfile(config_member)
            if config_stream is None:
                raise PolicyError("docker archive config is not a file")
            actual = sha256_bytes(config_stream.read())
            if actual != match.group(1):
                raise PolicyError("docker archive config checksum mismatch")
            return f"sha256:{actual}"
    except (KeyError, json.JSONDecodeError, tarfile.TarError) as exc:
        raise PolicyError(f"docker archive is malformed ({exc})") from exc


def read_member(stream: BinaryIO, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(min(remaining, 1024 * 1024))
        if not chunk:
            raise PolicyError("rootfs archive member ended unexpectedly")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def normalize_runtime_file(
    image_name: str, name: str, content: bytes
) -> tuple[bytes, list[str]]:
    if image_name != "web" or name not in {
        NEXT_PRERENDER_MANIFEST,
        NEXT_SERVER_REFERENCE_JSON,
        NEXT_SERVER_REFERENCE_JS,
    }:
        return content, []
    try:
        if name == NEXT_SERVER_REFERENCE_JS:
            prefix = "self.__RSC_SERVER_MANIFEST="
            source = content.decode("utf-8")
            if not source.startswith(prefix):
                raise ValueError("unexpected JavaScript wrapper")
            manifest = json.loads(json.loads(source.removeprefix(prefix)))
        else:
            manifest = json.loads(content)
        if not isinstance(manifest, dict):
            raise ValueError("manifest is not an object")
        if name == NEXT_PRERENDER_MANIFEST:
            preview = manifest.get("preview")
            if not isinstance(preview, dict):
                raise ValueError("preview object is missing")
            fields = [
                "previewModeEncryptionKey",
                "previewModeId",
                "previewModeSigningKey",
            ]
            for field in fields:
                if not isinstance(preview.get(field), str) or not preview[field]:
                    raise ValueError(f"{field} is missing")
                preview[field] = NORMALIZED_SECRET
            normalized = [f"preview.{field}" for field in fields]
        else:
            if (
                not isinstance(manifest.get("encryptionKey"), str)
                or not manifest["encryptionKey"]
            ):
                raise ValueError("encryptionKey is missing")
            manifest["encryptionKey"] = NORMALIZED_SECRET
            normalized = ["encryptionKey"]
        canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        if name == NEXT_SERVER_REFERENCE_JS:
            canonical = prefix + json.dumps(canonical)
        return canonical.encode("utf-8"), normalized
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
        raise PolicyError(f"{image_name}: cannot normalize {name}: {exc}") from exc


def rootfs_manifest(archive: Path, image_name: str) -> dict[str, Any]:
    prefixes = IMAGE_PREFIXES.get(image_name)
    if prefixes is None:
        raise PolicyError(f"{image_name}: no application-file boundary configured")
    entries: list[dict[str, Any]] = []
    with tarfile.open(archive, mode="r:*") as rootfs:
        for member in rootfs:
            name = member.name.lstrip("./")
            if not any(
                name == prefix or name.startswith(prefix) for prefix in prefixes
            ):
                continue
            kind = "other"
            digest: str | None = None
            target: str | None = None
            normalized_fields: list[str] = []
            if member.isfile():
                kind = "file"
                stream = rootfs.extractfile(member)
                if stream is None:
                    raise PolicyError(f"{image_name}: cannot read rootfs member {name}")
                content, normalized_fields = normalize_runtime_file(
                    image_name, name, read_member(stream, member.size)
                )
                digest = sha256_bytes(content)
            elif member.isdir():
                kind = "directory"
            elif member.issym():
                kind = "symlink"
                target = member.linkname
            elif member.islnk():
                kind = "hardlink"
                target = member.linkname
            entries.append(
                {
                    "kind": kind,
                    "mode": f"{stat.S_IMODE(member.mode):04o}",
                    "normalized_fields": normalized_fields,
                    "path": name,
                    "sha256": digest,
                    "size": member.size,
                    "target": target,
                }
            )
    if not entries:
        raise PolicyError(f"{image_name}: application-file manifest is empty")
    return {
        "entries": sorted(entries, key=lambda item: item["path"]),
        "image": image_name,
        "prefixes": list(prefixes),
        "schema_version": 1,
    }


def normalize_scan(
    document: dict[str, Any], image_name: str, sbom_sha256: str
) -> dict[str, Any]:
    matches = document.get("matches")
    descriptor = document.get("descriptor")
    source = document.get("source")
    if not isinstance(matches, list) or not isinstance(descriptor, dict):
        raise PolicyError(f"{image_name}: malformed Grype JSON")
    if not isinstance(source, dict):
        raise PolicyError(f"{image_name}: Grype source descriptor is missing")
    target = source.get("target")
    if isinstance(target, dict):
        target["userInput"] = f"sbom:{image_name}:{sbom_sha256}"
    descriptor.pop("configuration", None)
    document["matches"] = sorted(
        matches,
        key=lambda item: (
            str(item.get("vulnerability", {}).get("id", "")),
            str(item.get("artifact", {}).get("purl", "")),
            str(item.get("artifact", {}).get("name", "")),
            str(item.get("artifact", {}).get("version", "")),
        ),
    )
    document["ignoredMatches"] = sorted(
        document.get("ignoredMatches", []),
        key=lambda item: json.dumps(item, sort_keys=True),
    )
    document["slaifEvidence"] = {
        "image": image_name,
        "sbom_sha256": sbom_sha256,
    }
    return document


def find_values(value: object, key_names: set[str]) -> list[object]:
    found: list[object] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.casefold() in key_names:
                found.append(nested)
            found.extend(find_values(nested, key_names))
    elif isinstance(value, list):
        for nested in value:
            found.extend(find_values(nested, key_names))
    return found


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def validate_database_status(
    document: dict[str, Any], maximum_age_hours: int
) -> dict[str, Any]:
    timestamps = [
        parsed
        for value in find_values(document, {"built", "buildtime", "builtat"})
        if (parsed := parse_timestamp(value)) is not None
    ]
    if not timestamps:
        raise PolicyError("Grype database status has no build timestamp")
    built = max(timestamps)
    age_hours = (datetime.now(UTC) - built.astimezone(UTC)).total_seconds() / 3600
    if age_hours < -1 or age_hours > maximum_age_hours:
        raise PolicyError(
            f"Grype database age {age_hours:.1f}h exceeds {maximum_age_hours}h"
        )
    checksums = [
        str(value)
        for value in find_values(document, {"checksum"})
        if isinstance(value, str) and re.search(r"[0-9a-f]{64}", value)
    ]
    if not checksums:
        raise PolicyError("Grype database status has no SHA-256 checksum")
    return {
        "age_hours_at_validation": round(age_hours, 3),
        "built": built.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "checksum": sorted(checksums)[0],
    }


def normalize_database_status(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("valid") is not True or not document.get("schemaVersion"):
        raise PolicyError("Grype database status is invalid")
    source = document.get("from")
    if not isinstance(source, str):
        raise PolicyError("Grype database status has no source URL")
    values = parse_qs(urlparse(source).query).get("checksum", [])
    if len(values) != 1 or not re.fullmatch(r"sha256:[0-9a-f]{64}", values[0]):
        raise PolicyError("Grype database source has no SHA-256 checksum")
    document["checksum"] = values[0]
    return document


def purl_type(package: dict[str, Any]) -> str:
    for reference in package.get("externalRefs", []):
        locator = str(reference.get("referenceLocator", ""))
        if reference.get("referenceType") == "purl" and locator.startswith("pkg:"):
            return locator[4:].split("/", 1)[0]
    return "unclassified"


def match_is_excepted(
    match: dict[str, Any], image_name: str, exceptions: list[dict[str, Any]]
) -> bool:
    identifier = str(match.get("vulnerability", {}).get("id", ""))
    artifact = match.get("artifact", {})
    affected = str(artifact.get("purl") or "")
    for exception in exceptions:
        if (
            exception["identifier"] == identifier
            and exception["affected"] == affected
            and exception["scope"] == image_name
        ):
            return True
    return False


def validate_labels(image_name: str, metadata: dict[str, Any], revision: str) -> None:
    if image_name == "postgres":
        return
    labels = metadata.get("labels")
    if not isinstance(labels, dict):
        raise PolicyError(f"{image_name}: normalized image labels are missing")
    expected = {
        "org.opencontainers.image.created": FIXED_CREATED,
        "org.opencontainers.image.licenses": "Apache-2.0",
        "org.opencontainers.image.revision": revision,
        "org.opencontainers.image.source": (
            "https://github.com/ulfe-lmi/slaif-agent-site"
        ),
        "org.opencontainers.image.version": "0.0.0",
    }
    for key, value in expected.items():
        if labels.get(key) != value:
            raise PolicyError(f"{image_name}: OCI label {key} is {labels.get(key)!r}")
    for key in (
        "org.opencontainers.image.title",
        "org.opencontainers.image.description",
    ):
        if not labels.get(key):
            raise PolicyError(f"{image_name}: OCI label {key} is empty")


def validate_expected_components(
    image_name: str, document: dict[str, Any], expected: list[str]
) -> None:
    names = {str(item.get("name", "")).casefold() for item in document["packages"]}
    for component in expected:
        lowered = component.casefold()
        if not any(lowered == name or lowered in name for name in names):
            sample = ", ".join(sorted(names)[:12])
            raise PolicyError(
                f"{image_name}: expected SBOM component {component!r} absent; "
                f"sample={sample}"
            )
    if image_name == "browser-worker":
        forbidden = {"firefox", "webkit"}
        found = sorted(
            name for name in names if any(item in name for item in forbidden)
        )
        if found:
            raise PolicyError(
                "browser-worker: forbidden product browser inventory present: "
                + ", ".join(found)
            )


def scan_bundle_forbidden_content(root: Path, policy: dict[str, Any]) -> None:
    forbidden = [
        *policy["evidence"]["forbidden_host_prefixes"],
        *policy["evidence"]["forbidden_secret_markers"],
    ]
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        content = path.read_bytes().lower()
        for marker in forbidden:
            if marker.casefold().encode("utf-8") in content:
                raise PolicyError(
                    f"{path.relative_to(root)}: forbidden evidence marker {marker!r}"
                )
        if re.search(rb"-----begin [a-z ]*private key-----", content):
            raise PolicyError(
                f"{path.relative_to(root)}: private key material detected"
            )


def finalize_bundle(root: Path, revision: str) -> dict[str, Any]:
    policy = load_json(ROOT / POLICY_PATH.relative_to(ROOT))
    validate_policy(policy)
    vulnerability_document = load_json(
        ROOT / VULNERABILITY_EXCEPTIONS_PATH.relative_to(ROOT)
    )
    maximum_days = policy["vulnerability_policy"]["maximum_exception_days"]
    validate_exceptions(vulnerability_document, "vulnerability", maximum_days)
    database_status = load_json(root / "scanner/grype-database.json")
    database = validate_database_status(
        database_status,
        policy["vulnerability_policy"]["maximum_database_age_hours"],
    )
    images: list[dict[str, Any]] = []
    total_severities: Counter[str] = Counter()
    actual_critical: set[tuple[str, str, str]] = set()
    matched_critical: set[tuple[str, str, str]] = set()
    for image_name, configured in sorted(policy["required_images"].items()):
        metadata = load_json(root / f"images/{image_name}.json")
        validate_labels(image_name, metadata, revision)
        sbom_path = root / f"sboms/{image_name}.spdx.json"
        scan_sbom_path = root / f"scan-sboms/{image_name}.syft.json"
        scan_path = root / f"scans/{image_name}.grype.json"
        sbom = load_json(sbom_path)
        scan_sbom = load_json(scan_sbom_path)
        scan = load_json(scan_path)
        if scan_sbom.get("slaifEvidence", {}).get("image_id") != metadata["image_id"]:
            raise PolicyError(f"{image_name}: scan SBOM image identity is missing")
        if scan.get("slaifEvidence") != {
            "image": image_name,
            "sbom_sha256": sha256_file(scan_sbom_path),
        }:
            raise PolicyError(f"{image_name}: scan source SBOM checksum mismatch")
        validate_expected_components(
            image_name, sbom, configured["expected_components"]
        )
        severities: Counter[str] = Counter()
        unexcepted_critical: list[str] = []
        critical_findings: list[dict[str, str]] = []
        for match in scan.get("matches", []):
            severity = str(match.get("vulnerability", {}).get("severity", "Unknown"))
            severities[severity] += 1
            total_severities[severity] += 1
            if severity == "Critical":
                identifier = str(match.get("vulnerability", {}).get("id", "UNKNOWN"))
                artifact = match.get("artifact", {})
                affected = str(artifact.get("purl") or "")
                key = (identifier, affected, image_name)
                actual_critical.add(key)
                excepted = match_is_excepted(
                    match, image_name, vulnerability_document["exceptions"]
                )
                if excepted:
                    matched_critical.add(key)
                else:
                    unexcepted_critical.append(identifier)
                critical_findings.append(
                    {
                        "affected": affected,
                        "identifier": identifier,
                        "scope": image_name,
                        "status": "excepted" if excepted else "unexcepted",
                    }
                )
        if unexcepted_critical:
            raise PolicyError(
                f"{image_name}: unexcepted Critical vulnerabilities: "
                + ", ".join(sorted(set(unexcepted_critical)))
            )
        (root / f"scans/{image_name}.txt").write_text(
            "\n".join(
                [
                    f"image: {image_name}",
                    "gate: PASS (zero unexcepted Critical)",
                    f"Critical: {severities.get('Critical', 0)}",
                    "Critical exceptions: "
                    f"{len(critical_findings) - len(unexcepted_critical)}",
                    f"High: {severities.get('High', 0)} (review evidence)",
                    f"Medium: {severities.get('Medium', 0)}",
                    f"Low: {severities.get('Low', 0)}",
                    f"Negligible: {severities.get('Negligible', 0)}",
                    f"Unknown: {severities.get('Unknown', 0)}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        package_counts = Counter(purl_type(item) for item in sbom["packages"])
        unknown_licenses = sum(
            item.get("licenseDeclared") in {None, "", "NOASSERTION"}
            for item in sbom["packages"]
        )
        images.append(
            {
                "base_reference": policy["oci_sources"][configured["base"]],
                "critical_findings": critical_findings,
                "image": image_name,
                "image_id": metadata["image_id"],
                "local_reference": configured["local_reference"],
                "os_runtime_unknown_license_count": unknown_licenses,
                "package_counts_by_purl_type": dict(sorted(package_counts.items())),
                "package_count": len(sbom["packages"]),
                "sbom": str(sbom_path.relative_to(root)),
                "sbom_sha256": sha256_file(sbom_path),
                "scan": str(scan_path.relative_to(root)),
                "scan_sha256": sha256_file(scan_path),
                "scan_sbom": str(scan_sbom_path.relative_to(root)),
                "scan_sbom_sha256": sha256_file(scan_sbom_path),
                "severity_counts": dict(sorted(severities.items())),
                "unexcepted_critical": 0,
            }
        )
    exception_keys = {
        (entry["identifier"], entry["affected"], entry["scope"])
        for entry in vulnerability_document["exceptions"]
    }
    unused = sorted(exception_keys - actual_critical)
    if unused:
        details = ", ".join("/".join(item) for item in unused)
        raise PolicyError(
            "vulnerability exceptions: unused or stale exception(s): " + details
        )
    if matched_critical != actual_critical:
        missing = sorted(actual_critical - matched_critical)
        details = ", ".join("/".join(item) for item in missing)
        raise PolicyError(
            "vulnerability exceptions: unexcepted Critical finding(s): " + details
        )
    index = {
        "database": database,
        "exception_counts": {
            "license": len(
                load_json(ROOT / "supply-chain/license-exceptions.json")["exceptions"]
            ),
            "vulnerability": len(vulnerability_document["exceptions"]),
        },
        "images": images,
        "revision": revision,
        "scanner_tools": policy["scanner_tools"],
        "schema_version": 1,
        "severity_totals": dict(sorted(total_severities.items())),
    }
    write_json(root / "index.json", index)
    summary = [
        "SLAIF Agent-Site supply-chain evidence",
        f"revision: {revision}",
        f"images: {len(images)}",
        f"grype_database_built: {database['built']}",
        f"grype_database_checksum: {database['checksum']}",
        "vulnerability_gate: PASS (zero unexcepted Critical)",
        "high_findings: "
        f"{total_severities.get('High', 0)} (visible review evidence; not clean)",
        "browser_binary_inventory: empty",
    ]
    (root / "SUMMARY.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    scan_bundle_forbidden_content(root, policy)
    checksum_path = root / "SHA256SUMS"
    if checksum_path.exists():
        checksum_path.unlink()
    paths = sorted(path for path in root.rglob("*") if path.is_file())
    checksum_path.write_text(
        "".join(f"{sha256_file(path)}  {path.relative_to(root)}\n" for path in paths),
        encoding="utf-8",
    )
    return index


def validate_bundle(root: Path) -> None:
    policy = load_json(ROOT / POLICY_PATH.relative_to(ROOT))
    checksum_path = root / "SHA256SUMS"
    lines = checksum_path.read_text(encoding="utf-8").splitlines()
    recorded: dict[str, str] = {}
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\n]+)", line)
        if match is None or match.group(2) in recorded:
            raise PolicyError("SHA256SUMS: malformed or duplicate entry")
        recorded[match.group(2)] = match.group(1)
    actual = {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path != checksum_path
    }
    if recorded != actual:
        raise PolicyError("SHA256SUMS: missing, extra, or tampered evidence file")
    index = load_json(root / "index.json")
    if index.get("schema_version") != policy["evidence"]["required_index_version"]:
        raise PolicyError("index.json: schema version drift")
    if len(index.get("images", [])) != 6:
        raise PolicyError("index.json: required six-image coverage is missing")
    scan_bundle_forbidden_content(root, policy)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    metadata = subparsers.add_parser("normalize-image-metadata")
    metadata.add_argument("--input", required=True)
    metadata.add_argument("--output", type=Path, required=True)

    spdx = subparsers.add_parser("normalize-sbom")
    spdx.add_argument("--input", required=True)
    spdx.add_argument("--output", type=Path, required=True)
    spdx.add_argument("--image-name", required=True)
    spdx.add_argument("--image-id", required=True)
    spdx.add_argument("--source-revision", required=True)

    syft = subparsers.add_parser("normalize-scan-sbom")
    syft.add_argument("--input", required=True)
    syft.add_argument("--output", type=Path, required=True)
    syft.add_argument("--image-name", required=True)
    syft.add_argument("--image-id", required=True)
    syft.add_argument("--archive-config-id", required=True)
    syft.add_argument("--source-revision", required=True)

    archive_id = subparsers.add_parser("archive-config-id")
    archive_id.add_argument("--archive", type=Path, required=True)

    manifest = subparsers.add_parser("rootfs-manifest")
    manifest.add_argument("--archive", type=Path, required=True)
    manifest.add_argument("--output", type=Path, required=True)
    manifest.add_argument("--image-name", required=True)

    compare = subparsers.add_parser("compare-builds")
    compare.add_argument("--first-sbom", type=Path, required=True)
    compare.add_argument("--second-sbom", type=Path, required=True)
    compare.add_argument("--first-files", type=Path, required=True)
    compare.add_argument("--second-files", type=Path, required=True)
    compare.add_argument("--first-metadata", type=Path, required=True)
    compare.add_argument("--second-metadata", type=Path, required=True)
    compare.add_argument("--output", type=Path, required=True)
    compare.add_argument("--image-name", required=True)

    scan = subparsers.add_parser("normalize-scan")
    scan.add_argument("--input", required=True)
    scan.add_argument("--output", type=Path, required=True)
    scan.add_argument("--image-name", required=True)
    scan.add_argument("--sbom-sha256", required=True)

    database = subparsers.add_parser("normalize-database-status")
    database.add_argument("--input", required=True)
    database.add_argument("--output", type=Path, required=True)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--evidence", type=Path, required=True)
    finalize.add_argument("--revision", required=True)

    validate = subparsers.add_parser("validate-bundle")
    validate.add_argument("--evidence", type=Path, required=True)

    arguments = parser.parse_args()
    try:
        if arguments.command == "normalize-image-metadata":
            write_json(
                arguments.output,
                normalize_image_metadata(read_json(arguments.input)),
            )
        elif arguments.command == "normalize-sbom":
            write_json(
                arguments.output,
                normalize_spdx(
                    read_json(arguments.input),
                    arguments.image_name,
                    arguments.image_id,
                    arguments.source_revision,
                ),
            )
        elif arguments.command == "archive-config-id":
            print(docker_archive_config_id(arguments.archive))
        elif arguments.command == "normalize-scan-sbom":
            write_json(
                arguments.output,
                normalize_syft_sbom(
                    read_json(arguments.input),
                    arguments.image_name,
                    arguments.image_id,
                    arguments.archive_config_id,
                    arguments.source_revision,
                ),
            )
        elif arguments.command == "rootfs-manifest":
            write_json(
                arguments.output,
                rootfs_manifest(arguments.archive, arguments.image_name),
            )
        elif arguments.command == "compare-builds":
            first_sbom = load_json(arguments.first_sbom)
            second_sbom = load_json(arguments.second_sbom)
            first_files = load_json(arguments.first_files)
            second_files = load_json(arguments.second_files)
            if package_signature(first_sbom) != package_signature(second_sbom):
                raise PolicyError(
                    f"{arguments.image_name}: normalized SBOM package drift"
                )
            if first_files != second_files:
                raise PolicyError(
                    f"{arguments.image_name}: normalized application-file drift"
                )
            first_metadata = load_json(arguments.first_metadata)
            second_metadata = load_json(arguments.second_metadata)
            write_json(
                arguments.output,
                {
                    "application_files_equal": True,
                    "image": arguments.image_name,
                    "image_ids_equal": (
                        first_metadata["image_id"] == second_metadata["image_id"]
                    ),
                    "nondeterministic_oci_boundary": (
                        "image IDs may differ because Docker/OCI layer creation "
                        "timestamps are outside the normalized contract"
                    ),
                    "package_manifests_equal": True,
                    "schema_version": 1,
                },
            )
        elif arguments.command == "normalize-scan":
            if not re.fullmatch(r"[0-9a-f]{64}", arguments.sbom_sha256):
                raise PolicyError("SBOM SHA-256 is malformed")
            write_json(
                arguments.output,
                normalize_scan(
                    read_json(arguments.input),
                    arguments.image_name,
                    arguments.sbom_sha256,
                ),
            )
        elif arguments.command == "normalize-database-status":
            write_json(
                arguments.output,
                normalize_database_status(read_json(arguments.input)),
            )
        elif arguments.command == "finalize":
            index = finalize_bundle(arguments.evidence.resolve(), arguments.revision)
            print(
                "supply-chain-evidence: OK "
                f"images={len(index['images'])} "
                f"critical={index['severity_totals'].get('Critical', 0)} "
                f"high={index['severity_totals'].get('High', 0)}"
            )
        else:
            validate_bundle(arguments.evidence.resolve())
            print("supply-chain-evidence-checksum: OK")
    except (OSError, PolicyError, tarfile.TarError) as exc:
        print(f"supply-chain-evidence: ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
