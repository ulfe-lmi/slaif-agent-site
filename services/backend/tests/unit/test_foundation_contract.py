"""Metadata, public-API, lock, and package-content qualification tests."""

from __future__ import annotations

import ast
import email.parser
import hashlib
import importlib
import importlib.metadata
import re
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version
from slaif_agent_site.agent_state import foundation
from slaif_agent_site.db.migrations import migration_heads, migration_history

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
FOUNDATION_VERSION = "0.2.0"
FOUNDATION_WHEEL_SHA256 = (
    "c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1"
)
FOUNDATION_SDIST_SHA256 = (
    "eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c"
)
ALEMBIC_VERSION = "1.19.1"
ALEMBIC_WHEEL_SHA256 = (
    "b39018cb3d9413a19cbd54cf3c02ad33998641f0538eb77413a488a21c3e14be"
)
ALEMBIC_SDIST_SHA256 = (
    "e0fca0518118c78acc493e31bcb5402f190057aaf6df8b5b95ce94c4789cf648"
)
SQLALCHEMY_VERSION = "2.0.52"
SQLALCHEMY_PY3_WHEEL_SHA256 = (
    "3b81b8363a919ce53453591cdb93702e6bd54ade6c4fa2f468fc053baee5ed89"
)
SQLALCHEMY_SDIST_SHA256 = (
    "5e2d46356ac2ccb7d268ab6c2319ac6a2b42f1b8d5fd8bd3d46855cd82abee97"
)
EXPECTED_PUBLIC_API = {
    "CowConflict",
    "CowConflictError",
    "CowPostgresConfig",
    "CowPrivilegeValidation",
    "CowReviewer",
    "CowSession",
    "DiscardResult",
    "PromotionResult",
    "asyncpg_cow_reviewer",
    "asyncpg_cow_session",
    "deploy_cow_functions",
    "enable_cow_schema",
    "get_cow_conflicts",
    "get_operation_dependencies",
    "get_session_operations",
    "harden_cow_schema",
    "validate_cow_schema_privileges",
}
NEW_PACKAGE_FILES = {
    "slaif_agent_site/agent_api/__init__.py",
    "slaif_agent_site/agent_api/__main__.py",
    "slaif_agent_site/agent_api/app.py",
    "slaif_agent_site/application.py",
    "slaif_agent_site/authority.py",
    "slaif_agent_site/bootstrap/__init__.py",
    "slaif_agent_site/bootstrap/__main__.py",
    "slaif_agent_site/bootstrap/config.py",
    "slaif_agent_site/bootstrap/service.py",
    "slaif_agent_site/config.py",
    "slaif_agent_site/control_api/__init__.py",
    "slaif_agent_site/control_api/__main__.py",
    "slaif_agent_site/control_api/app.py",
    "slaif_agent_site/correlation.py",
    "slaif_agent_site/db/__init__.py",
    "slaif_agent_site/db/alembic/env.py",
    "slaif_agent_site/db/alembic/script.py.mako",
    "slaif_agent_site/db/alembic/versions/006_001_postgres_bootstrap.py",
    "slaif_agent_site/db/connections.py",
    "slaif_agent_site/db/executor.py",
    "slaif_agent_site/db/migrations.py",
    "slaif_agent_site/db/privileges.py",
    "slaif_agent_site/db/readiness.py",
    "slaif_agent_site/db/roles.py",
    "slaif_agent_site/editor_api/__init__.py",
    "slaif_agent_site/editor_api/__main__.py",
    "slaif_agent_site/editor_api/app.py",
    "slaif_agent_site/errors.py",
    "slaif_agent_site/health.py",
    "slaif_agent_site/logging.py",
    "slaif_agent_site/mcp_adapter/__init__.py",
    "slaif_agent_site/mcp_adapter/__main__.py",
    "slaif_agent_site/mcp_adapter/app.py",
    "slaif_agent_site/media_gc/__init__.py",
    "slaif_agent_site/media_gc/__main__.py",
    "slaif_agent_site/media_service/__init__.py",
    "slaif_agent_site/media_service/__main__.py",
    "slaif_agent_site/media_service/app.py",
    "slaif_agent_site/render_api/__init__.py",
    "slaif_agent_site/render_api/__main__.py",
    "slaif_agent_site/render_api/app.py",
    "slaif_agent_site/review_worker/__init__.py",
    "slaif_agent_site/review_worker/__main__.py",
    "slaif_agent_site/scheduler/__init__.py",
    "slaif_agent_site/scheduler/__main__.py",
    "slaif_agent_site/worker.py",
}
EXPECTED_PACKAGE_FILES = NEW_PACKAGE_FILES | {
    "slaif_agent_site/__init__.py",
    "slaif_agent_site/agent_state/__init__.py",
    "slaif_agent_site/agent_state/foundation.py",
}
EXPECTED_SDIST_FILES = {
    "alembic.ini",
    "LICENSE",
    "NOTICE",
    "PKG-INFO",
    "README.md",
    "pyproject.toml",
    "pyproject.toml.orig",
    "services/backend/src/slaif_agent_site/__init__.py",
    "services/backend/src/slaif_agent_site/agent_state/__init__.py",
    "services/backend/src/slaif_agent_site/agent_state/foundation.py",
    "migrations/alembic/README.md",
    "migrations/alembic/__init__.py",
    "migrations/bootstrap/README.md",
} | {f"services/backend/src/{path}" for path in NEW_PACKAGE_FILES}


def _load_toml(relative: str) -> dict[str, object]:
    with (REPOSITORY_ROOT / relative).open("rb") as handle:
        return tomllib.load(handle)


def _package_record(lock: dict[str, object], name: str) -> dict[str, object]:
    packages = lock["package"]
    assert isinstance(packages, list)
    matches = [
        package
        for package in packages
        if isinstance(package, dict) and package.get("name") == name
    ]
    assert len(matches) == 1
    return matches[0]


def test_exact_distribution_and_public_imports() -> None:
    assert importlib.metadata.version("agent-cow-postgresql") == FOUNDATION_VERSION
    assert importlib.import_module("agentcow")
    public_module = importlib.import_module("agentcow.postgres")
    assert EXPECTED_PUBLIC_API <= set(public_module.__all__)
    assert set(foundation.QUALIFIED_PUBLIC_API) == EXPECTED_PUBLIC_API
    assert foundation.FOUNDATION_DISTRIBUTION == "agent-cow-postgresql"
    assert foundation.FOUNDATION_VERSION == FOUNDATION_VERSION
    for symbol in EXPECTED_PUBLIC_API:
        assert getattr(foundation, symbol) is getattr(public_module, symbol)


def test_adapter_is_only_a_documented_public_import_boundary() -> None:
    source_path = Path(foundation.__file__)
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    foundation_imports = [
        node for node in imports if node.module == "agentcow.postgres"
    ]

    assert len(foundation_imports) == 1
    assert {alias.name for alias in foundation_imports[0].names} == EXPECTED_PUBLIC_API
    assert all(not alias.name.startswith("_") for alias in foundation_imports[0].names)
    assert all(node.module in {"__future__", "agentcow.postgres"} for node in imports)
    assert not re.search(
        r"\b(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", source
    )
    assert "_base" not in source
    assert "_changes" not in source
    assert "native" not in source


def test_python_and_package_metadata_ranges_are_coherent() -> None:
    project = _load_toml("pyproject.toml")["project"]
    assert isinstance(project, dict)
    assert project["name"] == "slaif-agent-site"
    assert project["version"] == "0.0.0"
    assert project["requires-python"] == ">=3.12,<3.15"
    assert project["license"] == "Apache-2.0"
    assert project["readme"] == "README.md"
    assert project["dependencies"] == [
        "agent-cow-postgresql==0.2.0",
        "alembic==1.19.1",
        "asyncpg==0.31.0",
        "fastapi==0.141.1",
        "pydantic==2.13.4",
        "pydantic-settings==2.15.0",
        "sqlalchemy==2.0.52",
        "uvicorn==0.52.3",
    ]

    build_system = _load_toml("pyproject.toml")["build-system"]
    assert isinstance(build_system, dict)
    assert build_system == {
        "requires": ["uv_build==0.12.5"],
        "build-backend": "uv_build",
    }

    foundation_metadata = importlib.metadata.metadata("agent-cow-postgresql")
    assert foundation_metadata["License-Expression"] == "MIT"
    foundation_python = SpecifierSet(foundation_metadata["Requires-Python"])
    product_python = SpecifierSet(str(project["requires-python"]))
    for version in (Version("3.12"), Version("3.13"), Version("3.14")):
        assert version in product_python
        assert version in foundation_python

    product_metadata = importlib.metadata.metadata("slaif-agent-site")
    assert product_metadata["Version"] == "0.0.0"
    assert SpecifierSet(product_metadata["Requires-Python"]) == product_python
    assert product_metadata["License-Expression"] == "Apache-2.0"
    assert product_metadata["Description-Content-Type"] == "text/markdown"


def test_lock_uses_exact_verified_registry_artifacts() -> None:
    lock = _load_toml("uv.lock")
    package = _package_record(lock, "agent-cow-postgresql")

    assert package["version"] == FOUNDATION_VERSION
    assert package["source"] == {"registry": "https://pypi.org/simple"}
    sdist = package["sdist"]
    wheels = package["wheels"]
    assert isinstance(sdist, dict)
    assert isinstance(wheels, list)
    assert sdist["hash"] == f"sha256:{FOUNDATION_SDIST_SHA256}"
    wheel_hashes = {
        wheel["hash"] for wheel in wheels if isinstance(wheel, dict) and "hash" in wheel
    }
    assert f"sha256:{FOUNDATION_WHEEL_SHA256}" in wheel_hashes

    serialized = repr(package).lower()
    assert "git+" not in serialized
    assert "editable" not in serialized
    assert "'git'" not in serialized
    assert "'path'" not in serialized
    assert "'url':" not in repr(package["source"]).lower()


def test_migration_dependencies_are_exact_registry_artifacts() -> None:
    lock = _load_toml("uv.lock")
    expectations = {
        "alembic": (
            ALEMBIC_VERSION,
            ALEMBIC_SDIST_SHA256,
            ALEMBIC_WHEEL_SHA256,
        ),
        "sqlalchemy": (
            SQLALCHEMY_VERSION,
            SQLALCHEMY_SDIST_SHA256,
            SQLALCHEMY_PY3_WHEEL_SHA256,
        ),
    }
    for name, (version, sdist_hash, wheel_hash) in expectations.items():
        package = _package_record(lock, name)
        assert package["version"] == version
        assert package["source"] == {"registry": "https://pypi.org/simple"}
        assert package["sdist"]["hash"] == f"sha256:{sdist_hash}"  # type: ignore[index]
        wheels = package["wheels"]
        assert isinstance(wheels, list)
        assert f"sha256:{wheel_hash}" in {
            wheel["hash"] for wheel in wheels if isinstance(wheel, dict)
        }
        serialized = repr(package).casefold()
        assert not any(
            marker in serialized for marker in ("git+", "editable", "'path'")
        )

    licenses = {
        "alembic": ("MIT", None),
        "SQLAlchemy": (None, "MIT"),
        "greenlet": ("MIT AND PSF-2.0", None),
        "Mako": ("MIT", None),
        "MarkupSafe": ("BSD-3-Clause", None),
    }
    for name, (expression, legacy) in licenses.items():
        metadata = importlib.metadata.metadata(name)
        assert metadata.get("License-Expression") == expression
        assert metadata.get("License") == legacy


def test_built_distributions_have_bounded_contents_and_metadata(
    tmp_path: Path,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("slaif_agent_site-0.0.0-*.whl"))
    sdist = tmp_path / "slaif_agent_site-0.0.0.tar.gz"
    assert sdist.is_file()

    with zipfile.ZipFile(wheel) as archive:
        wheel_names = set(archive.namelist())
        package_files = {
            name
            for name in wheel_names
            if name.startswith("slaif_agent_site/") and not name.endswith("/")
        }
        assert package_files == EXPECTED_PACKAGE_FILES
        metadata_name = next(
            name for name in wheel_names if name.endswith(".dist-info/METADATA")
        )
        metadata_bytes = archive.read(metadata_name)

    with tarfile.open(sdist, mode="r:gz") as archive:
        sdist_names = {member.name for member in archive.getmembers()}
        sdist_files = {
            member.name.split("/", maxsplit=1)[1]
            for member in archive.getmembers()
            if member.isfile()
        }
        assert sdist_files == EXPECTED_SDIST_FILES

    all_names = wheel_names | sdist_names
    forbidden_parts = (
        "/.env",
        "/.git/",
        "/__pycache__/",
        "/oap/",
        "/tests/",
        ".coverage",
        ".pem",
        ".pyc",
    )
    assert not any(part in name for name in all_names for part in forbidden_parts)
    assert not any("secret" in name.lower() for name in all_names)
    assert all(
        name.startswith("slaif_agent_site-0.0.0.dist-info/")
        for name in wheel_names
        if not name.startswith("slaif_agent_site/")
    )

    metadata = email.parser.BytesParser().parsebytes(metadata_bytes)
    assert metadata["Name"] == "slaif-agent-site"
    assert metadata["Version"] == "0.0.0"
    assert metadata["License-Expression"] == "Apache-2.0"
    assert SpecifierSet(metadata["Requires-Python"]) == SpecifierSet(">=3.12,<3.15")
    assert metadata.get_all("Requires-Dist") == [
        "agent-cow-postgresql==0.2.0",
        "alembic==1.19.1",
        "asyncpg==0.31.0",
        "fastapi==0.141.1",
        "pydantic==2.13.4",
        "pydantic-settings==2.15.0",
        "sqlalchemy==2.0.52",
        "uvicorn==0.52.3",
    ]


def test_locked_foundation_artifact_hash_constants_are_sha256() -> None:
    for digest in (FOUNDATION_WHEEL_SHA256, FOUNDATION_SDIST_SHA256):
        assert len(digest) == hashlib.sha256().digest_size * 2
        assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_alembic_graph_and_offline_sql_need_no_locator_or_network() -> None:
    assert migration_heads() == ("006_001",)
    assert migration_history() == ("006_001",)
    config = (REPOSITORY_ROOT / "alembic.ini").read_text(encoding="utf-8")
    assert "sqlalchemy.url" not in config
    assert "://" not in config
    assert "password" not in config.casefold()

    environment = {
        "PGHOST": "unreachable.invalid",
        "PGPORT": "1",
        "PGDATABASE": "must_not_connect",
    }
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            "alembic.ini",
            "upgrade",
            "head",
            "--sql",
        ],
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert "006_001" in completed.stdout
    assert 'CREATE SCHEMA IF NOT EXISTS "control"' in completed.stdout


def test_database_source_uses_public_foundation_boundary_and_no_domain_ddl() -> None:
    package = REPOSITORY_ROOT / "services/backend/src/slaif_agent_site"
    database_source = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (package / "bootstrap", package / "db")
        for path in sorted(root.rglob("*.py"))
    )
    assert "from agentcow" not in database_source
    assert "import agentcow" not in database_source
    assert "allow_unsafe_canonical_writes=False" in database_source
    assert "allow_deferred_fks=True" in database_source
    assert "Schema 'content' has no COW-enabled tables" not in database_source
    assert "EMPTY_SAFE" in database_source
    assert "HARDENED" in database_source
    assert not any(
        marker in database_source.casefold()
        for marker in ("psycopg", "boto3", "supabase", "cloud sql")
    )

    revision = (
        package / "db/alembic/versions/006_001_postgres_bootstrap.py"
    ).read_text(encoding="utf-8")
    assert revision.count("CREATE TABLE") == 1
    assert '"control"."bootstrap_readiness"' in revision
    assert '"readiness_state" text' in revision
    assert "'PENDING'" in revision
    assert "'EMPTY_SAFE'" in revision
    assert "'HARDENED'" in revision
    forbidden_tables = (
        "workspace",
        "capability",
        "content_item",
        "page_composition",
        "audit_event",
        "media_asset",
        "site_membership",
    )
    assert not any(f'CREATE TABLE "{name}"' in revision for name in forbidden_tables)
