"""
Unit test verifying user-friendly translation and structured presentation
of SAP Service Layer errors (e.g. invalid UDFs, non-existent fields, duplicate keys, constraints).
"""
import pytest
from unittest.mock import MagicMock
import httpx

from app.sap.client import sap_client
from app.agent.tools import format_friendly_creation_error


def test_parse_invalid_udf_property():
    """Verify raw code -1000 with custom field U_VSG is humanized cleanly."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": {
            "code": -1000,
            "message": {
                "lang": "en-us",
                "value": "Property 'U_VSG' of 'BusinessPartner' is invalid"
            }
        }
    }
    parsed = sap_client._parse_sap_error(mock_resp)
    assert "Property 'U_VSG' of 'BusinessPartner' is invalid" not in parsed or "Field 'U_VSG'" in parsed
    assert "U_VSG" in parsed
    assert "User-Defined Field" in parsed or "custom field" in parsed.lower()


def test_format_friendly_creation_error_for_u_vsg():
    """Verify format_friendly_creation_error formats U_VSG into actionable markdown."""
    raw_error = "SAP Error (Code -1000): Property 'U_VSG' of 'BusinessPartner' is invalid"
    friendly = format_friendly_creation_error(
        err_str=raw_error,
        entity="BusinessPartners",
        key_val="C10001",
        data={"CardCode": "C10001", "U_VSG": "Expenses"}
    )
    assert "❌ **Unable to Create Business Partner in SAP**" in friendly
    assert "U_VSG" in friendly
    assert "User-Defined Field (UDF)" in friendly
    assert "How to resolve" in friendly
    assert "Tools > Customization Tools > User-Defined Fields" in friendly


def test_format_friendly_creation_error_for_duplicate():
    """Verify duplicate record errors are humanized."""
    raw_error = "SAP Error (Code -10): Item code 'FG0001' already exists"
    friendly = format_friendly_creation_error(
        err_str=raw_error,
        entity="Items",
        key_val="FG0001",
        data={"ItemCode": "FG0001"}
    )
    assert "Duplicate Identifier" in friendly
    assert "FG0001" in friendly
    assert "How to resolve" in friendly


def test_format_friendly_creation_error_for_constraint_reference():
    """Verify constraint/foreign key errors (e.g. GST 18%) are humanized."""
    raw_error = "SAP Constraint Error:  [OCRD.ECVatGroup] , 'Linked value GST 18% does not exist'"
    friendly = format_friendly_creation_error(
        err_str=raw_error,
        entity="BusinessPartners",
        key_val="C20001",
        data={"CardCode": "C20001", "VatGroup": "GST 18%"}
    )
    assert "Missing Master Data Reference" in friendly
    assert "GST 18%" in friendly
    assert "How to resolve" in friendly


@pytest.mark.asyncio
async def test_auto_heal_unconfigured_u_vsg(monkeypatch):
    """Verify execute_create_master_data auto-omits unconfigured U_VSG and succeeds on retry."""
    from unittest.mock import AsyncMock
    from app.agent.tools import execute_create_master_data
    from app.sap.business_partners import SAPBusinessPartnersService

    call_count = 0
    async def mock_create(bp_model):
        nonlocal call_count
        call_count += 1
        # First call fails because U_VSG is invalid
        if getattr(bp_model, "U_VSG", None):
            raise Exception("SAP Error (Code -1000): Property 'U_VSG' of 'BusinessPartner' is invalid")
        return {"CardCode": bp_model.CardCode, "CardName": bp_model.CardName}

    monkeypatch.setattr(SAPBusinessPartnersService, "create_business_partner", mock_create)
    monkeypatch.setattr(SAPBusinessPartnersService, "check_card_exists", AsyncMock(return_value=False))

    result = await execute_create_master_data(
        entity="BusinessPartners",
        data={"CardCode": "C99999", "CardName": "Auto Heal Test Corp", "U_VSG": "Expenses"}
    )
    assert result["success"] is True
    assert result["action"] == "CREATE_SUCCESS"
    assert "U_VSG" not in result["creation_draft"]
    assert call_count == 2
