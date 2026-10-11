"""Regression tests for request bounds, auth abuse throttles, and response headers."""

import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import _auth_limiter, app
from app.security import SlidingWindowLimiter


class SecurityControlsTest(unittest.TestCase):
    def test_sliding_window_limiter_expires_and_reports_retry_time(self) -> None:
        limiter = SlidingWindowLimiter()
        self.assertEqual(limiter.allow("login", "client", 2, 60, now=100), (True, 0))
        self.assertEqual(limiter.allow("login", "client", 2, 60, now=110), (True, 0))
        allowed, retry_after = limiter.allow("login", "client", 2, 60, now=120)
        self.assertFalse(allowed)
        self.assertEqual(retry_after, 40)
        self.assertEqual(limiter.allow("login", "client", 2, 60, now=161), (True, 0))

    def test_login_attempts_are_limited(self) -> None:
        _auth_limiter.clear()
        with patch.dict(os.environ, {"AUTH_MODE": "demo"}):
            client = TestClient(app, client=("198.51.100.40", 4321))
            for _ in range(10):
                self.assertEqual(client.post("/auth/login", json={"username": "unknown", "password": "wrong"}).status_code, 401)
            blocked = client.post("/auth/login", json={"username": "unknown", "password": "wrong"})
            self.assertEqual(blocked.status_code, 429)
            self.assertGreater(int(blocked.headers["retry-after"]), 0)

    def test_trusted_proxy_header_uses_forwarded_ip_for_limit_key(self) -> None:
        _auth_limiter.clear()
        env = {"AUTH_MODE": "demo", "TRUST_PROXY_HEADERS": "true"}
        with patch.dict(os.environ, env):
            client = TestClient(app, client=("10.0.0.8", 4321))
            for attempt in range(10):
                response = client.post("/auth/login", json={"username": "unknown", "password": "wrong"}, headers={"x-forwarded-for": f"198.51.100.{attempt + 1}"})
                self.assertEqual(response.status_code, 401)
            blocked = client.post("/auth/login", json={"username": "unknown", "password": "wrong"}, headers={"x-forwarded-for": "198.51.100.200"})
            self.assertEqual(blocked.status_code, 401)

    def test_large_json_body_is_rejected_before_auth_handler(self) -> None:
        with patch.dict(os.environ, {"AUTH_MODE": "demo"}):
            client = TestClient(app)
            response = client.post("/auth/login", content=b"{" + b" " * 1_048_576 + b"}", headers={"content-type": "application/json"})
            self.assertEqual(response.status_code, 413)

    def test_security_headers_are_present(self) -> None:
        with patch.dict(os.environ, {"AUTH_MODE": "demo"}):
            response = TestClient(app).get("/health")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])

    def test_api_docs_are_not_public_in_strict_mode(self) -> None:
        with patch.dict(os.environ, {"AUTH_MODE": "strict", "HEATWATCH_SESSION_SECRET": "security-test-secret-32-characters-long"}):
            client = TestClient(app)
            self.assertEqual(client.get("/openapi.json").status_code, 401)
            self.assertEqual(client.get("/docs").status_code, 401)


if __name__ == "__main__":
    unittest.main()
