"""Fixed local login-principal manifest contract."""

from slaif_agent_site.db.roles import DATABASE_LOGINS, LOGIN_NAMES, ROLE_NAMES


def test_local_login_manifest_is_exact_and_one_to_one() -> None:
    assert tuple(
        (login.name, login.privilege_role, login.secret_file_stem)
        for login in DATABASE_LOGINS
    ) == (
        ("slaif_bootstrap_login", "slaif_owner", "bootstrap"),
        ("slaif_control_login", "slaif_control", "control"),
        ("slaif_editor_login", "slaif_editor_runtime", "editor"),
        ("slaif_agent_login", "slaif_agent_runtime", "agent"),
        ("slaif_public_login", "slaif_public_reader", "public"),
        ("slaif_preview_login", "slaif_preview_reader", "preview"),
        ("slaif_reviewer_login", "slaif_reviewer", "reviewer"),
        ("slaif_scheduler_login", "slaif_scheduler", "scheduler"),
        ("slaif_media_login", "slaif_media", "media"),
        ("slaif_gc_login", "slaif_gc", "gc"),
    )
    assert len(set(LOGIN_NAMES)) == len(LOGIN_NAMES)
    assert {login.privilege_role for login in DATABASE_LOGINS} == set(ROLE_NAMES)
