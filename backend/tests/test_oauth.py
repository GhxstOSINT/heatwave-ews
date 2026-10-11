"""OAuth redirect integrity and strict-dashboard access tests (no provider network)."""

import os
import unittest
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
import requests

from app.main import app
from app.oauth import ProviderHTTPError, authorization_url, configured_providers, exchange_identity, make_pending, read_pending, safe_next


class OAuthContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mode = patch.dict(os.environ, {"AUTH_MODE": "demo", "HEATSAFE_GOOGLE_CLIENT_ID": "test-client", "HEATSAFE_GOOGLE_CLIENT_SECRET": "test-secret"}, clear=False)
        self.mode.start()

    def tearDown(self) -> None:
        self.mode.stop()

    def test_pending_state_is_signed_and_provider_bound(self) -> None:
        cookie, state, challenge = make_pending("google", "/dashboard.html?replay=bihar-june-2019")
        self.assertEqual(len(challenge), 43)
        self.assertEqual(read_pending(cookie, "google", state)["next"], "/dashboard.html?replay=bihar-june-2019")
        for bad_cookie, bad_provider, bad_state in ((cookie + "x", "google", state), (cookie, "github", state), (cookie, "google", "wrong")):
            with self.assertRaises(ValueError):
                read_pending(bad_cookie, bad_provider, bad_state)

    def test_only_configured_providers_are_enabled(self) -> None:
        with patch.dict(os.environ, {"HEATSAFE_GITHUB_CLIENT_ID": "", "HEATSAFE_GITHUB_CLIENT_SECRET": ""}):
            self.assertEqual(configured_providers(), ["google"])

    def test_microsoft_is_not_a_supported_provider(self) -> None:
        with patch.dict(os.environ, {"HEATSAFE_MICROSOFT_CLIENT_ID": "ignored", "HEATSAFE_MICROSOFT_CLIENT_SECRET": "ignored"}):
            self.assertNotIn("microsoft", configured_providers())
            with self.assertRaises(ValueError):
                make_pending("microsoft", "/dashboard.html")
            self.assertEqual(TestClient(app).get("/auth/oauth/microsoft/start").status_code, 404)

    def test_authorization_url_has_exact_callback_and_pkce(self) -> None:
        url = authorization_url("google", "http://localhost:8543/auth/oauth/google/callback", "state-1", "challenge-1")
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["redirect_uri"], ["http://localhost:8543/auth/oauth/google/callback"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["state"], ["state-1"])

    def test_next_never_becomes_external_redirect(self) -> None:
        self.assertEqual(safe_next("https://example.org"), "/dashboard.html")
        self.assertEqual(safe_next("//example.org"), "/dashboard.html")
        self.assertEqual(safe_next("/dashboard.html?replay=case"), "/dashboard.html?replay=case")

    def test_strict_mode_requires_session_for_map_api(self) -> None:
        with patch.dict(os.environ, {"AUTH_MODE": "strict", "HEATWATCH_SESSION_SECRET": "x" * 40}):
            client = TestClient(app)
            self.assertEqual(client.get("/districts").status_code, 401)
            self.assertEqual(client.get("/auth/config").status_code, 200)

    def test_first_time_google_identity_creates_viewer_and_session(self) -> None:
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://heatsafe.example", "DATABASE_URL": "postgresql://unused"}):
            client = TestClient(app, base_url="https://heatsafe.example")
            start = client.get("/auth/oauth/google/start", follow_redirects=False)
            self.assertEqual(start.status_code, 302)
            state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
            connection = MagicMock()
            connection.__enter__.return_value = connection
            cursor = connection.cursor.return_value.__enter__.return_value
            cursor.fetchone.return_value = None
            with patch("app.main.exchange_identity", return_value=("google-subject-1", "New viewer")), patch("app.main.psycopg.connect", return_value=connection):
                result = client.get("/auth/oauth/google/callback", params={"code": "test-code", "state": state}, follow_redirects=False)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "https://heatsafe.example/dashboard.html")
            self.assertIn("heatsafe_session=", result.headers["set-cookie"])
            statements = [call.args[0] for call in cursor.execute.call_args_list]
            self.assertTrue(any("INSERT INTO users" in statement and "'viewer'" in statement for statement in statements))
            self.assertTrue(any("INSERT INTO oauth_identities" in statement for statement in statements))

    def test_provider_configuration_failure_has_specific_recovery_code(self) -> None:
        with patch.dict(os.environ, {"PUBLIC_BASE_URL": "https://heatsafe.example"}):
            client = TestClient(app, base_url="https://heatsafe.example")
            start = client.get("/auth/oauth/google/start", follow_redirects=False)
            state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]
            provider_response = requests.Response()
            provider_response.status_code = 401
            with patch("app.main.exchange_identity", side_effect=requests.HTTPError(response=provider_response)):
                result = client.get("/auth/oauth/google/callback", params={"code": "test-code", "state": state}, follow_redirects=False)
            self.assertEqual(result.status_code, 303)
            self.assertEqual(result.headers["location"], "https://heatsafe.example/login.html?error=provider_setup")

    def test_provider_http_error_identifies_token_exchange_without_exposing_body(self) -> None:
        response = requests.Response()
        response.status_code = 401
        response._content = b'{"error":"invalid_client","client_secret":"do-not-log"}'
        with patch("app.oauth.requests.post", return_value=response):
            with self.assertRaises(ProviderHTTPError) as caught:
                exchange_identity("google", "code", "verifier", "https://heatsafe.example/auth/oauth/google/callback")
        self.assertEqual(caught.exception.phase, "token_exchange")
        self.assertEqual(caught.exception.response.status_code, 401)
        self.assertNotIn("do-not-log", str(caught.exception))

    def test_provider_http_error_identifies_userinfo(self) -> None:
        token_response = requests.Response()
        token_response.status_code = 200
        token_response._content = b'{"access_token":"test-token"}'
        identity_response = requests.Response()
        identity_response.status_code = 401
        with patch("app.oauth.requests.post", return_value=token_response), patch("app.oauth.requests.get", return_value=identity_response):
            with self.assertRaises(ProviderHTTPError) as caught:
                exchange_identity("google", "code", "verifier", "https://heatsafe.example/auth/oauth/google/callback")
        self.assertEqual(caught.exception.phase, "userinfo")
