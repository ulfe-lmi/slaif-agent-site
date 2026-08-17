"""Static route-equivalence checks for the two open-source edge adapters."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
ROUTES = {
    "/api/control/": "control-api:8000",
    "/api/editor/": "editor-api:8000",
    "/api/agent/": "agent-api:8000",
    "/mcp/": "mcp-adapter:8000",
    "/media/": "media-service:8000",
    "/": "web:3000",
}


class EdgeContractTests(unittest.TestCase):
    def test_route_contract_is_equivalent(self) -> None:
        nginx = (ROOT / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
        apache = (ROOT / "infra/apache/slaif-agent-site.conf").read_text(
            encoding="utf-8"
        )
        for prefix, upstream in ROUTES.items():
            self.assertIn(f"location {prefix}", nginx)
            self.assertIn(f"http://{upstream}", nginx)
            self.assertIn(f"ProxyPass        {prefix} http://{upstream}/", apache)

    def test_browser_and_render_are_not_edge_upstreams(self) -> None:
        for path in (
            ROOT / "infra/nginx/nginx.conf",
            ROOT / "infra/apache/slaif-agent-site.conf",
        ):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("browser-worker:", content)
            self.assertNotIn("render-api:", content)


if __name__ == "__main__":
    unittest.main()
