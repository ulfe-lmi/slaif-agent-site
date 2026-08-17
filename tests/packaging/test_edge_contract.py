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
CSP = (
    "default-src 'self'; base-uri 'none'; object-src 'none'; "
    "frame-ancestors 'none'; form-action 'self'; script-src 'self'; "
    "style-src 'self'; img-src 'self' data:; font-src 'self'; "
    "connect-src 'self'"
)


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

    def test_csp_contract_is_equivalent_and_self_hosted(self) -> None:
        nginx = (ROOT / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
        apache = (ROOT / "infra/apache/slaif-agent-site.conf").read_text(
            encoding="utf-8"
        )
        self.assertEqual(nginx.count(f'Content-Security-Policy "{CSP}"'), 1)
        self.assertEqual(apache.count(f'Content-Security-Policy "{CSP}"'), 1)
        self.assertEqual(nginx.count("add_header Content-Security-Policy"), 1)
        self.assertEqual(nginx.count("proxy_hide_header Content-Security-Policy;"), 1)
        self.assertEqual(apache.count("Header always set Content-Security-Policy"), 1)
        self.assertEqual(apache.count("unset Content-Security-Policy"), 2)
        for content in (nginx, apache):
            for directive in (
                "default-src 'self'",
                "base-uri 'none'",
                "object-src 'none'",
                "frame-ancestors 'none'",
                "form-action 'self'",
                "script-src 'self'",
                "style-src 'self'",
                "img-src 'self' data:",
                "connect-src 'self'",
            ):
                self.assertIn(directive, content)
            for forbidden in (
                "unsafe-inline",
                "unsafe-eval",
                "report-uri",
                "report-to",
                "http:",
                "https:",
                "wss:",
                "*",
            ):
                self.assertNotIn(forbidden, CSP)

    def test_one_edge_owned_request_id_replaces_upstream_and_caller_values(
        self,
    ) -> None:
        nginx = (ROOT / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
        apache = (ROOT / "infra/apache/slaif-agent-site.conf").read_text(
            encoding="utf-8"
        )
        self.assertEqual(nginx.count("add_header X-Request-ID $request_id always;"), 1)
        self.assertEqual(nginx.count("proxy_set_header X-Request-ID $request_id;"), 1)
        self.assertEqual(nginx.count("proxy_hide_header X-Request-ID;"), 1)
        self.assertEqual(
            apache.count('RequestHeader set X-Request-ID "%{UNIQUE_ID}e"'), 1
        )
        self.assertEqual(
            apache.count('Header always set X-Request-ID "%{UNIQUE_ID}e"'), 1
        )
        self.assertEqual(apache.count("unset X-Request-ID"), 2)


if __name__ == "__main__":
    unittest.main()
