"""
Unit tests for SAP Service Layer client and allowlist enforcement.
"""
import pytest
from app.sap.client import SAPClientError, sap_client

@pytest.mark.asyncio
async def test_allowlist_enforcement():
    # Attempting to query an unapproved entity must raise security violation
    with pytest.raises(SAPClientError) as exc_info:
        await sap_client.get("ArbitraryTable")
    assert "Security Violation" in str(exc_info.value)

@pytest.mark.asyncio
async def test_safe_mock_item_creation_and_duplicate(monkeypatch):
    # Test safe development simulation isolated from live SAP server
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "")
    sap_client._mock_records["Items"].clear()

    item_payload = {
        "ItemCode": "TEST-ITEM-999",
        "ItemName": "Test Simulated Item",
        "ItemsGroupCode": 100
    }
    # First creation succeeds
    res = await sap_client.post("Items", item_payload)
    assert res.get("ItemCode") == "TEST-ITEM-999"

    # Second creation with identical key triggers duplicate detection
    with pytest.raises(SAPClientError) as exc_info:
        await sap_client.post("Items", item_payload)
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_sap_health_check_unconfigured(monkeypatch):
    """When SAP is not configured or placeholder, check_health must return connected=False."""
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "https://YOUR_SAP_SERVER:50000/b1s/v2")
    monkeypatch.setattr(settings, "sap_password", "YOUR_SAP_PASSWORD")
    if hasattr(sap_client, '_health_cache'):
        sap_client._health_cache = {}

    health = await sap_client.check_health()
    assert health["connected"] is False
    assert health["status"] == "UNCONFIGURED"


@pytest.mark.asyncio
async def test_sap_health_check_disconnected_on_failure(monkeypatch):
    """When SAP server is unreachable or fails login, check_health must return connected=False."""
    from app.config import settings
    monkeypatch.setattr(settings, "sap_service_layer_url", "https://103.89.45.237:50000/b1s/v2")
    monkeypatch.setattr(settings, "sap_company_db", "TEST_DB")
    monkeypatch.setattr(settings, "sap_username", "user")
    monkeypatch.setattr(settings, "sap_password", "secret")
    if hasattr(sap_client, '_health_cache'):
        sap_client._health_cache = {}

    async def mock_failed_login(*args, **kwargs):
        return False, "SAP Service Layer timed out after 3.5s (SAP server is stuck or unreachable)", {
            "status": "TIMEOUT",
            "error_code": "TIMEOUT"
        }

    monkeypatch.setattr(sap_client.auth, "login", mock_failed_login)
    health = await sap_client.check_health()
    assert health["connected"] is False
    assert health["status"] in ["TIMEOUT", "DISCONNECTED"]
    assert "timed out" in health["message"].lower() or "stuck" in health["message"].lower()

