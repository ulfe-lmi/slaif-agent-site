"""Static route-equivalence checks for the two open-source edge adapters."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
ROUTES = {
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
            if prefix == "/api/editor/":
                self.assertIn(
                    "ProxyPass        /api/editor/v1/ http://editor-api:8000/api/editor/v1/",
                    apache,
                )
            else:
                self.assertIn(f"ProxyPass        {prefix} http://{upstream}/", apache)

    def test_control_health_is_adapted_and_v1_path_is_preserved(self) -> None:
        nginx = (ROOT / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
        apache = (ROOT / "infra/apache/slaif-agent-site.conf").read_text(
            encoding="utf-8"
        )
        for leaf in ("live", "ready"):
            self.assertIn(f"location = /api/control/health/{leaf}", nginx)
            self.assertIn(f"control-api:8000/health/{leaf}", nginx)
            self.assertIn(f"/api/control/health/{leaf}", apache)
        self.assertIn("proxy_pass http://control-api:8000;", nginx)
        self.assertIn("location /api/control/v1/", nginx)
        self.assertIn(
            "ProxyPass        /api/control/v1/ http://control-api:8000/api/control/v1/",
            apache,
        )
        self.assertNotIn("location /api/control/ {\n            proxy_pass", nginx)
        self.assertIn("ProxyPass        /api/control/ !", apache)

    def test_agent_health_aliases_and_prefix_preserving_route(self) -> None:
        nginx = (ROOT / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
        for leaf in ("live", "ready"):
            self.assertIn(f"location = /api/agent/health/{leaf}", nginx)
            self.assertIn(f"proxy_pass http://agent-api:8000/health/{leaf};", nginx)
        self.assertIn("location /api/agent/", nginx)
        self.assertIn("proxy_pass http://agent-api:8000;", nginx)
        self.assertNotIn(
            "location /api/agent/ {\n            proxy_pass http://agent-api:8000/;",
            nginx,
        )

    def test_editor_health_aliases_and_versioned_prefix_preserving_route(self) -> None:
        nginx = (ROOT / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
        apache = (ROOT / "infra/apache/slaif-agent-site.conf").read_text(
            encoding="utf-8"
        )
        for leaf in ("live", "ready"):
            self.assertIn(f"location = /api/editor/health/{leaf}", nginx)
            self.assertIn(f"proxy_pass http://editor-api:8000/health/{leaf};", nginx)
            self.assertIn(f"/api/editor/health/{leaf}", apache)
        self.assertIn("location /api/editor/v1/", nginx)
        self.assertIn("proxy_pass http://editor-api:8000;", nginx)
        self.assertIn(
            "ProxyPass        /api/editor/v1/ http://editor-api:8000/api/editor/v1/",
            apache,
        )
        self.assertIn("ProxyPass        /api/editor/ !", apache)

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
        self.assertEqual(nginx.count("map $uri $slaif_csp"), 1)
        self.assertEqual(nginx.count("'nonce-$request_id'"), 2)
        self.assertEqual(apache.count("'nonce-%{UNIQUE_ID}e'"), 3)
        self.assertEqual(nginx.count("add_header Content-Security-Policy"), 1)
        self.assertEqual(nginx.count("proxy_set_header Content-Security-Policy"), 1)
        self.assertEqual(apache.count("RequestHeader set Content-Security-Policy"), 1)
        self.assertEqual(nginx.count("proxy_hide_header Content-Security-Policy;"), 1)
        self.assertEqual(apache.count("Header always set Content-Security-Policy"), 2)
        self.assertEqual(apache.count("unset Content-Security-Policy"), 2)
        for content in (nginx, apache):
            csp_lines = "\n".join(
                line for line in content.splitlines() if "default-src" in line
            )
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
                self.assertIn(directive, csp_lines)
            policies = csp_lines.splitlines()
            public_policy = next(
                line for line in policies if "style-src-attr" not in line
            )
            editor_policy = next(line for line in policies if "style-src-attr" in line)
            for forbidden in (
                "unsafe-inline",
                "unsafe-eval",
                "report-uri",
                "report-to",
                "http:",
                "https:",
                "wss:",
            ):
                self.assertNotIn(forbidden, public_policy)
            self.assertNotIn(" * ", public_policy)
            self.assertIn("style-src-elem 'self' 'unsafe-inline'", editor_policy)
            self.assertIn("style-src-attr 'unsafe-inline'", editor_policy)
            self.assertNotIn("unsafe-eval", editor_policy)

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
