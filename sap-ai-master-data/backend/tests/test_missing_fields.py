"""
Unit tests for missing field engine.
Verifies all mandatory fields for Item, BP, and Warehouse.
"""
from app.models.extraction import MasterDataType
from app.services.missing_fields import missing_field_engine

def test_missing_fields_for_item():
    empty_data = {}
    missing = missing_field_engine.identify_missing_fields(MasterDataType.ITEM, empty_data)
    fields = [m.field for m in missing]
    expected_mandatory = [
        "ItemCode", "ItemName", "ItemsGroupCode", "InventoryUOM", "ItemType",
        "TaxRate", "ItemManagementMethod", "ItemCategory", "MaterialType",
        "HSN", "TaxCategory"
    ]
    for exp in expected_mandatory:
        assert exp in fields, f"Expected mandatory field '{exp}' not identified in missing fields"

    # Fully populated item should have 0 missing fields
    full_data = {
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
    missing_full = missing_field_engine.identify_missing_fields(MasterDataType.ITEM, full_data)
    assert len(missing_full) == 0

def test_missing_fields_for_business_partner():
    empty_data = {}
    missing = missing_field_engine.identify_missing_fields(MasterDataType.BUSINESS_PARTNER, empty_data)
    fields = [m.field for m in missing]
    expected_mandatory = [
        "CardCode", "CardName", "Address", "TaxDetails",
        "PaymentTerms", "Currency", "ControlAccount", "GSTNo", "PANNo"
    ]
    for exp in expected_mandatory:
        assert exp in fields, f"Expected mandatory field '{exp}' not identified in missing fields"

    # Full BP data
    full_data = {
        "CardCode": "V10024",
        "CardName": "Apex Precision Components Ltd",
        "Address": "Plot 42, Industrial Area Phase 2",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "211000",
        "GSTNo": "27AABCU9603R1ZM",
        "PANNo": "AABCU9603R"
    }
    missing_full = missing_field_engine.identify_missing_fields(MasterDataType.BUSINESS_PARTNER, full_data)
    assert len(missing_full) == 0

def test_missing_fields_for_warehouse():
    empty_data = {}
    missing = missing_field_engine.identify_missing_fields(MasterDataType.WAREHOUSE, empty_data)
    fields = [m.field for m in missing]
    expected_mandatory = ["WarehouseCode", "WarehouseName", "Location", "Address"]
    for exp in expected_mandatory:
        assert exp in fields, f"Expected mandatory field '{exp}' not identified in missing fields"

    # Full warehouse data
    full_data = {
        "WarehouseCode": "WH01",
        "WarehouseName": "Central Distribution Depot",
        "Location": 1,
        "Address": "100 Logistics Way, Industrial Park"
    }
    missing_full = missing_field_engine.identify_missing_fields(MasterDataType.WAREHOUSE, full_data)
    assert len(missing_full) == 0
