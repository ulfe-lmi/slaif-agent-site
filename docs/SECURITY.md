# Render resolution security boundary

The internal Render API owns one `slaif_public_login` connection pool with the
sole `slaif_public_reader` membership. Pool initialization verifies database,
login/current-user, and exact membership before readiness succeeds. Locator and
driver details are never returned or logged.

The role has no direct `control` relation access and no site management,
administrator, session, setup, migration, or publication function. It can call
only the two active site resolver functions. Resolution derives site identity
from normalized authority/path input and returns routing facts, not
authorization. Caller-provided identity, workspace, preview, membership, and
capability headers have no meaning. The endpoint is internal and has no edge,
Web, Control, Agent, Editor, or MCP route in this round.
