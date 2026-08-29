"""Focused tests for deterministic artifact manifest helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.supply_chain.reproducible import (
    artifact_manifest,
    clean_node_outputs,
    describe_manifest_difference,
    find_generated_contracts,
    tree_manifest,
)


class ReproducibilityHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write(self, relative: str, content: bytes = b"data") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_python_manifest_keeps_only_wheel_and_sdist(self) -> None:
        self.write("dist/example-1.0.0.whl", b"wheel")
        self.write("dist/example-1.0.0.tar.gz", b"sdist")
        self.write("dist/.gitignore", b"*")
        manifest = artifact_manifest(self.root / "dist")
        self.assertEqual(
            [entry["name"] for entry in manifest],
            ["example-1.0.0.tar.gz", "example-1.0.0.whl"],
        )

    def test_tree_manifest_is_sorted_and_content_sensitive(self) -> None:
        self.write("output/z.txt", b"z")
        first = self.write("output/a.txt", b"a")
        manifest = tree_manifest(self.root, ("output",))
        self.assertEqual(
            [entry["path"] for entry in manifest],
            ["output/a.txt", "output/z.txt"],
        )
        first.write_bytes(b"changed")
        self.assertNotEqual(manifest, tree_manifest(self.root, ("output",)))

    def test_web_manifest_includes_next_and_runtime_dependencies(self) -> None:
        manifest_path = (
            "apps/web/.next/standalone/apps/web/.next/prerender-manifest.json"
        )
        package_path = "apps/web/.next/standalone/node_modules/example/package.json"
        self.write(package_path, b'{"name":"example"}\n')

        def content(marker: str, version: int = 1) -> bytes:
            return json.dumps(
                {
                    "preview": {
                        "previewModeEncryptionKey": marker * 2,
                        "previewModeId": marker * 3,
                        "previewModeSigningKey": marker * 4,
                    },
                    "version": version,
                }
            ).encode()

        target = ("apps/web/.next/standalone",)
        self.write(manifest_path, content("a"))
        first = tree_manifest(self.root, target)
        paths = {entry["path"] for entry in first}
        self.assertIn(manifest_path, paths)
        self.assertIn(package_path, paths)

        self.write(manifest_path, content("b"))
        self.assertEqual(first, tree_manifest(self.root, target))
        self.write(manifest_path, content("b", version=2))
        self.assertNotEqual(first, tree_manifest(self.root, target))

    def test_next_route_manifest_compares_json_semantics(self) -> None:
        manifest_path = (
            "apps/web/.next/standalone/apps/web/.next/app-path-routes-manifest.json"
        )
        target = ("apps/web/.next/standalone",)
        self.write(manifest_path, b'{"a":[{"b":1}],"z":"same"}')
        first = tree_manifest(self.root, target)
        self.write(manifest_path, b'{"z":"same","a":[{"b":1}]}')
        self.assertEqual(first, tree_manifest(self.root, target))
        self.write(manifest_path, b'{"z":"changed","a":[{"b":1}]}')
        second = tree_manifest(self.root, target)
        self.assertNotEqual(first, second)
        difference = describe_manifest_difference(
            {
                "browser_runtime": [],
                "web_distribution": first,
                "workspace_outputs": [],
            },
            {
                "browser_runtime": [],
                "web_distribution": second,
                "workspace_outputs": [],
            },
        )
        self.assertIn("json-path=$.z", difference)

    def test_generated_contracts_ignore_build_cache_but_reject_source_output(
        self,
    ) -> None:
        self.write("apps/web/.next/openapi.json")
        self.assertEqual(find_generated_contracts(self.root), [])
        self.write("generated/openapi.json")
        self.assertEqual(
            find_generated_contracts(self.root), ["generated/openapi.json"]
        )

    def test_clean_node_outputs_targets_only_known_build_directories(self) -> None:
        self.write("apps/web/.next/output.js")
        self.write("packages/example/dist/output.js")
        retained = self.write("packages/example/src/index.ts")
        clean_node_outputs(self.root)
        self.assertFalse((self.root / "apps/web/.next").exists())
        self.assertFalse((self.root / "packages/example/dist").exists())
        self.assertTrue(retained.is_file())

    def test_manifest_difference_is_bounded_and_hash_only(self) -> None:
        first = {
            "browser_runtime": [],
            "web_distribution": [
                {"path": "opt/slaif/a.js", "sha256": "a" * 64, "size": 1}
            ],
            "workspace_outputs": [],
        }
        second = {
            "browser_runtime": [],
            "web_distribution": [
                {"path": "opt/slaif/a.js", "sha256": "b" * 64, "size": 1}
            ],
            "workspace_outputs": [],
        }
        difference = describe_manifest_difference(first, second)
        self.assertIn("path=opt/slaif/a.js", difference)
        self.assertIn("sha256=", difference)
        self.assertNotIn("data", difference)


if __name__ == "__main__":
    unittest.main()
