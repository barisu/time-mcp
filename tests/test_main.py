import os
import unittest
from unittest.mock import patch

from main import DEFAULT_ALLOWED_ORIGINS, create_mcp


class CreateMCPTests(unittest.TestCase):
    def test_localhost_defaults_are_preserved_with_custom_origin(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            mcp = create_mcp(["--allow-origin", "https://app.example.com"])

        transport_security = mcp.settings.transport_security

        self.assertIsNotNone(transport_security)
        for origin in DEFAULT_ALLOWED_ORIGINS:
            self.assertIn(origin, transport_security.allowed_origins)
        self.assertIn("https://app.example.com", transport_security.allowed_origins)

    def test_comma_separated_origins_are_supported(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            mcp = create_mcp(["--allow-origin", "https://a.example.com,https://b.example.com"])

        transport_security = mcp.settings.transport_security

        self.assertIsNotNone(transport_security)
        self.assertIn("https://a.example.com", transport_security.allowed_origins)
        self.assertIn("https://b.example.com", transport_security.allowed_origins)

    def test_env_allowed_origins_are_merged(self) -> None:
        with patch.dict(
            os.environ,
            {"FASTMCP_ALLOWED_ORIGINS": "https://env.example.com"},
            clear=True,
        ):
            mcp = create_mcp([])

        transport_security = mcp.settings.transport_security

        self.assertIsNotNone(transport_security)
        self.assertIn("https://env.example.com", transport_security.allowed_origins)

    def test_non_local_bind_keeps_default_transport_security_disabled(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            mcp = create_mcp(["--host", "192.0.2.10"])

        self.assertIsNone(mcp.settings.transport_security)

    def test_concrete_bind_host_infers_allowed_host_for_custom_origins(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            mcp = create_mcp(
                [
                    "--host",
                    "192.0.2.10",
                    "--allow-origin",
                    "https://app.example.com",
                ]
            )

        transport_security = mcp.settings.transport_security

        self.assertIsNotNone(transport_security)
        self.assertIn("192.0.2.10:*", transport_security.allowed_hosts)
        self.assertIn("https://app.example.com", transport_security.allowed_origins)

    def test_wildcard_host_requires_explicit_allowed_hosts(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "Allowed origins require allowed hosts"):
                create_mcp(["--host", "0.0.0.0", "--allow-origin", "https://app.example.com"])

    def test_wildcard_host_accepts_explicit_allowed_hosts(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            mcp = create_mcp(
                [
                    "--host",
                    "0.0.0.0",
                    "--allow-host",
                    "mcp.example.com:*",
                    "--allow-origin",
                    "https://app.example.com",
                ]
            )

        transport_security = mcp.settings.transport_security

        self.assertIsNotNone(transport_security)
        self.assertIn("mcp.example.com:*", transport_security.allowed_hosts)
        self.assertIn("https://app.example.com", transport_security.allowed_origins)


if __name__ == "__main__":
    unittest.main()
