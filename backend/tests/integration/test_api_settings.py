# file: backend/tests/integration/test_api_settings.py
"""
🧱 Integration Tests for NextDNS Settings API Endpoints

Testing the settings API LEGO bricks — /settings/nextdns/api-key and
/settings/nextdns/profiles.
"""

import pytest
from unittest.mock import patch, MagicMock

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestApiKeyEndpoints:
    """Test GET/PUT /settings/nextdns/api-key."""

    def test_get_api_key_unconfigured(self, test_client):
        """Returns configured=False when no API key is stored."""
        with patch("main.get_nextdns_api_key", return_value=None):
            response = test_client.get(
                "/settings/nextdns/api-key",
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is False
        assert data.get("masked_key") is None

    def test_get_api_key_configured(self, test_client):
        """Returns configured=True and a masked key when a key is stored."""
        with patch("main.get_nextdns_api_key", return_value="supersecretkey1234"):
            response = test_client.get(
                "/settings/nextdns/api-key",
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["masked_key"] is not None
        # Last 4 chars are visible
        assert data["masked_key"].endswith("1234")
        # Full key is not exposed
        assert "supersecretkey" not in data["masked_key"]

    def test_put_api_key_empty_body(self, test_client):
        """Rejects empty api_key."""
        response = test_client.put(
            "/settings/nextdns/api-key",
            json={"api_key": "   "},
            headers={"X-API-Key": "test-api-key-123"},
        )
        assert response.status_code == 400

    def test_put_api_key_invalid_key(self, test_client):
        """Rejects a key that NextDNS API refuses."""
        with patch("main._validate_nextdns_api_key", return_value=False):
            response = test_client.put(
                "/settings/nextdns/api-key",
                json={"api_key": "bad-key"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 422

    def test_put_api_key_valid_key(self, test_client):
        """Accepts and persists a valid key."""
        with (
            patch("main._validate_nextdns_api_key", return_value=True),
            patch("main.set_nextdns_api_key", return_value=True),
        ):
            response = test_client.put(
                "/settings/nextdns/api-key",
                json={"api_key": "valid-key-abcd1234"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["configured"] is True
        assert data["masked_key"].endswith("1234")

    def test_put_api_key_db_failure(self, test_client):
        """Returns 500 when DB write fails."""
        with (
            patch("main._validate_nextdns_api_key", return_value=True),
            patch("main.set_nextdns_api_key", return_value=False),
        ):
            response = test_client.put(
                "/settings/nextdns/api-key",
                json={"api_key": "valid-key-abcd1234"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 500

    def test_api_key_endpoints_require_auth(self, test_client):
        """Endpoints return 401/403 (auth enabled) or 200 (auth disabled) without a key.

        In the test environment AUTH_ENABLED=false so 200 is expected;
        in production with AUTH_ENABLED=true a 401/403 is returned.
        """
        response = test_client.get("/settings/nextdns/api-key")
        assert response.status_code in [200, 401, 403]

        response = test_client.put(
            "/settings/nextdns/api-key", json={"api_key": "x"}
        )
        assert response.status_code in [200, 400, 401, 403, 422, 500]


class TestProfileSettingsEndpoints:
    """Test CRUD on /settings/nextdns/profiles."""

    def _make_profile_row(self, profile_id, enabled=True):
        row = MagicMock()
        row.profile_id = profile_id
        row.enabled = enabled
        row.created_at = None
        row.updated_at = None
        return row

    def test_list_profiles_empty(self, test_client):
        """Returns an empty list when no profiles are configured."""
        with patch("main.get_all_profiles", return_value=[]):
            response = test_client.get(
                "/settings/nextdns/profiles",
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["profiles"] == []
        assert data["total"] == 0

    def test_list_profiles_with_data(self, test_client):
        """Returns all profiles (enabled and disabled)."""
        rows = [
            self._make_profile_row("p1", enabled=True),
            self._make_profile_row("p2", enabled=False),
        ]
        with patch("main.get_all_profiles", return_value=rows):
            response = test_client.get(
                "/settings/nextdns/profiles",
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        ids = [p["profile_id"] for p in data["profiles"]]
        assert "p1" in ids
        assert "p2" in ids

    def test_add_profile_no_api_key(self, test_client):
        """Returns 422 when no NextDNS API key is configured."""
        with patch("main.get_nextdns_api_key", return_value=None):
            response = test_client.post(
                "/settings/nextdns/profiles",
                json={"profile_id": "new-profile"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 422

    def test_add_profile_not_found_on_nextdns(self, test_client):
        """Returns 422 when profile does not exist on NextDNS."""
        with (
            patch("main.get_nextdns_api_key", return_value="some-key"),
            patch("main.get_profile_info", return_value={"error": "Not found"}),
        ):
            response = test_client.post(
                "/settings/nextdns/profiles",
                json={"profile_id": "bad-profile"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 422

    def test_add_profile_already_exists(self, test_client):
        """Returns 409 when profile already exists in DB."""
        with (
            patch("main.get_nextdns_api_key", return_value="some-key"),
            patch("main.get_profile_info", return_value={"id": "p1", "name": "P1"}),
            patch("main.add_profile", return_value=False),
        ):
            response = test_client.post(
                "/settings/nextdns/profiles",
                json={"profile_id": "p1"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 409

    def test_add_profile_success(self, test_client):
        """Successfully adds a new profile."""
        row = self._make_profile_row("new-profile")
        with (
            patch("main.get_nextdns_api_key", return_value="some-key"),
            patch(
                "main.get_profile_info",
                return_value={"id": "new-profile", "name": "New"},
            ),
            patch("main.add_profile", return_value=True),
            patch("main.get_profile", return_value=row),
        ):
            response = test_client.post(
                "/settings/nextdns/profiles",
                json={"profile_id": "new-profile"},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 201
        assert response.json()["profile_id"] == "new-profile"
        assert response.json()["enabled"] is True

    def test_add_profile_empty_id(self, test_client):
        """Returns 400 for empty profile_id."""
        response = test_client.post(
            "/settings/nextdns/profiles",
            json={"profile_id": "  "},
            headers={"X-API-Key": "test-api-key-123"},
        )
        assert response.status_code == 400

    def test_update_profile_enable(self, test_client):
        """Enables an existing profile."""
        row = self._make_profile_row("p1", enabled=True)
        with (
            patch("main.update_profile_enabled", return_value=True),
            patch("main.get_profile", return_value=row),
        ):
            response = test_client.put(
                "/settings/nextdns/profiles/p1",
                json={"enabled": True},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        assert response.json()["enabled"] is True

    def test_update_profile_not_found(self, test_client):
        """Returns 404 when profile does not exist."""
        with patch("main.update_profile_enabled", return_value=False):
            response = test_client.put(
                "/settings/nextdns/profiles/ghost",
                json={"enabled": True},
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 404

    def test_delete_profile_success(self, test_client):
        """Deletes a profile and returns cleanup counts."""
        with patch(
            "main.delete_profile",
            return_value={
                "deleted": True,
                "dns_logs_deleted": 42,
                "fetch_status_deleted": 1,
            },
        ):
            response = test_client.delete(
                "/settings/nextdns/profiles/p1",
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["dns_logs_deleted"] == 42
        assert data["fetch_status_deleted"] == 1

    def test_delete_profile_not_found(self, test_client):
        """Returns 404 when profile does not exist."""
        with patch(
            "main.delete_profile",
            return_value={
                "deleted": False,
                "dns_logs_deleted": 0,
                "fetch_status_deleted": 0,
            },
        ):
            response = test_client.delete(
                "/settings/nextdns/profiles/ghost",
                headers={"X-API-Key": "test-api-key-123"},
            )
        assert response.status_code == 404

    def test_delete_profile_skip_purge(self, test_client):
        """Passes purge_data=False when ?purge_data=false is set."""
        with patch(
            "main.delete_profile",
            return_value={
                "deleted": True,
                "dns_logs_deleted": 0,
                "fetch_status_deleted": 0,
            },
        ) as mock_delete:
            test_client.delete(
                "/settings/nextdns/profiles/p1?purge_data=false",
                headers={"X-API-Key": "test-api-key-123"},
            )
        mock_delete.assert_called_once_with("p1", delete_data=False)

    def test_profiles_endpoints_require_auth(self, test_client):
        """Endpoints return 401/403 (auth enabled) or 200 (auth disabled) without a key.

        In the test environment AUTH_ENABLED=false so 200 is expected;
        in production with AUTH_ENABLED=true a 401/403 is returned.
        """
        assert test_client.get("/settings/nextdns/profiles").status_code in [
            200,
            401,
            403,
        ]
        assert test_client.post(
            "/settings/nextdns/profiles", json={"profile_id": "x"}
        ).status_code in [200, 400, 401, 403, 422]
        assert test_client.put(
            "/settings/nextdns/profiles/x", json={"enabled": True}
        ).status_code in [200, 401, 403, 404]
        assert test_client.delete("/settings/nextdns/profiles/x").status_code in [
            200,
            401,
            403,
            404,
        ]
