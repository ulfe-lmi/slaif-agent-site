# OAP Work Order — 090-a (inert until activated)

## Contract and objective

Implement and prove the self-hosted coordinated backup/restore baseline and
clean-deployment operational acceptance. Links: §§39, 46, 52.1/52.8. Requires
089; recheck the time-limited browser exception before activation.

## Production requirements and proof

Add documented, noninteractive Compose/operator tools for consistent PostgreSQL
and immutable public media backup plus safe restore into an explicitly empty
target. Preserve ownership/modes/digests; never bundle live secrets or private
credentials. Document single-host baseline, PITR production requirements,
RPO/RTO targets, rollback and destructive-target safeguards.

An automated clean restore test creates and accepts representative dynamic
site state, RBAC/delegation, audit, media and retained private review evidence;
backs up; destroys only a validated disposable test deployment; restores to a
fresh deployment; reruns migrations/COW hardening/privilege validation; verifies
canonical sites/routes/models/composition/theme/RBAC/audit/media, setup remains
closed, old capabilities/retrieval credentials are invalid, private artifacts
remain private and services/readiness work. Corrupt/incomplete/mismatched backup,
nonempty target and media digest mismatch fail closed.

Also run the exact clean-clone `docker compose up --build` contract with only
NGINX published and no hosted secret. Binary done requires actual recovered
product behavior, not documentation or object-unit tests. Run full packaging,
restore, license/SBOM/supply-chain and required CI. No release/production
deployment. Report `090-a-backup-restore-operational-proof.md` with SELF; no
merge/extra PR.
