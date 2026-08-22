# Critical Review Queue

PRs merged autonomously that require human post-merge review.
Focus: security boundaries, authorization logic, data integrity, trust model.

| PR | Objective | Risk | Decisions Taken | Priority |
|---|---|---|---|---|
| [#28](https://github.com/ulfe-lmi/slaif-agent-site/pull/28) | 015-a Editor API content model CRUD | **HIGH**: New HTTP routes expose content model CRUD. SECURITY DEFINER functions with `search_path=pg_catalog` prevent hijacking but the `privileges.py` allowlist was modified to permit `slaif_editor_runtime` EXECUTE on content schema functions. Verify this doesn't create a privilege escalation path. Soft-delete for content types preserves audit; hard-delete for fields may lose provenance. | Chose soft-delete for content types (audit trail), hard-delete for field definitions (simpler cleanup). Granted EXECUTE to both `slaif_editor_runtime` and `slaif_control` because editor routes serve authenticated human users and control API needs read access. Added content-model function names to the bootstrap post-harden grant list rather than modifying `harden_cow_schema` itself. | P1 - Review before production |
