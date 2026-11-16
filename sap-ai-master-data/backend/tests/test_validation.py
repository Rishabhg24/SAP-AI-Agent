"""
Unit tests for deterministic master data validation.
"""
import pytest
from app.services.validation_service import validation_service

def test_valid_item_master():
    data = {
        "ItemCode": "ITM-10024",
        "ItemName": "Stainless Steel Hex Bolt",
        "ItemsGroupCode": 100,
        "InventoryUOM": "PCS",
        "ItemType": "Inventory/Sales/Purchase",
        "TaxRate": "18%",
        "ItemManagementMethod": "Batch",
        "ItemCategory": "Item",
        "MaterialType": "RM",
        "HSN": "73181500",
        "TaxCategory": "Taxable"
    }
    res = validation_service.validate_item(data)
    assert res.valid is True
    assert len(res.missing_fields) == 0
    assert len(res.invalid_fields) == 0

def test_item_missing_mandatory_name():
    data = {
        "ItemCode": "ITM-10024"
        # ItemName and other mandatory fields missing
    }
    res = validation_service.validate_item(data)
    assert res.valid is False
    assert any(m.field == "ItemName" for m in res.missing_fields)
    assert any(m.field == "TaxRate" for m in res.missing_fields)
    assert any(m.field == "HSN" for m in res.missing_fields)

def test_business_partner_validation_and_card_type_mapping():
    # CardType provided as friendly 'Supplier'
    data = {
        "CardCode": "V90042",
        "CardName": "Apex Components Ltd",
        "CardType": "Supplier",
        "Address": "Plot 42, Industrial Area",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "211000",
        "GSTNo": "27AABCU9603R1ZM",
        "PANNo": "AABCU9603R"
    }
    res = validation_service.validate_business_partner(data)
    assert res.valid is True
    assert res.validated_data["CardType"] == "cSupplier"

def test_business_partner_card_code_length_limit():
    # CardCode > 15 chars should fail
    data = {
        "CardCode": "THIS_CODE_IS_TOO_LONG_FOR_SAP_B1",
        "CardName": "Invalid Length Partner",
        "CardType": "Customer",
        "Address": "Plot 42, Industrial Area",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "211000",
        "GSTNo": "27AABCU9603R1ZM",
        "PANNo": "AABCU9603R"
    }
    res = validation_service.validate_business_partner(data)
    assert res.valid is False
    assert any(inv.field == "CardCode" for inv in res.invalid_fields)

def test_warehouse_code_length_limit():
    # WarehouseCode > 8 chars should fail
    data = {
        "WarehouseCode": "LONG_WAREHOUSE_CODE",
        "WarehouseName": "Central Storage",
        "Location": 1,
        "Address": "100 Logistics Way"
    }
    res = validation_service.validate_warehouse(data)
    assert res.valid is False
    assert any(inv.field == "WarehouseCode" for inv in res.invalid_fields)

def test_valid_warehouse():
    data = {
        "WarehouseCode": "WH01",
        "WarehouseName": "Main Warehouse",
        "Location": 1,
        "Address": "100 Logistics Way, Industrial Park",
        "Inactive": False
    }
    res = validation_service.validate_warehouse(data)
    assert res.valid is True
    assert len(res.missing_fields) == 0
