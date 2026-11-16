"""
Unit tests for master data normalization service.
"""
import pytest
from app.services.normalization_service import normalization_service

def test_boolean_normalization():
    assert normalization_service.normalize_boolean("yes") is True
    assert normalization_service.normalize_boolean("YES") is True
    assert normalization_service.normalize_boolean("true") is True
    assert normalization_service.normalize_boolean("1") is True
    assert normalization_service.normalize_boolean("tYES") is True
    assert normalization_service.normalize_boolean(True) is True

    assert normalization_service.normalize_boolean("no") is False
    assert normalization_service.normalize_boolean("NO") is False
    assert normalization_service.normalize_boolean("false") is False
    assert normalization_service.normalize_boolean("0") is False
    assert normalization_service.normalize_boolean("tNO") is False
    assert normalization_service.normalize_boolean(False) is False

def test_code_field_casing_and_trimming():
    assert normalization_service.normalize_field_value("ItemCode", "  itm-10024  ") == "ITM-10024"
    assert normalization_service.normalize_field_value("CardCode", "  v90042  ") == "V90042"
    assert normalization_service.normalize_field_value("WarehouseCode", "  wh01  ") == "WH01"

def test_number_normalization():
    assert normalization_service.normalize_field_value("SalesUnitWeight", " 1,250.50 ") == 1250.5
    assert normalization_service.normalize_field_value("ItemsGroupCode", "100") == 100

def test_dict_normalization():
    raw = {
        "ItemCode": " itm-200 ",
        "ItemName": "  Steel Widget  ",
        "InventoryItem": "yes",
        "SalesItem": "no"
    }
    cleaned = normalization_service.normalize_dict(raw)
    assert cleaned["ItemCode"] == "ITM-200"
    assert cleaned["ItemName"] == "Steel Widget"
    assert cleaned["InventoryItem"] is True
    assert cleaned["SalesItem"] is False
