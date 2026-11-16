"""
Unit and integration tests for Excel spreadsheet input and extraction pipeline.
"""
import io
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
import openpyxl

from app.main import app
from app.models.extraction import ConflictStatus, MasterDataType
from app.services.extraction_service import extraction_service, load_spreadsheet_rows
from app.services.extraction_compare import extraction_comparator
from app.services.validation_service import validation_service
from app.utils.security import validate_document_content

client = TestClient(app)

def test_validate_document_content_xlsx():
    """Verify Excel magic bytes validation."""
    # ZIP magic bytes PK\x03\x04
    valid_content = b"PK\x03\x04\x14\x00\x06\x00sample_content"
    is_valid, msg, doc_type = validate_document_content(valid_content, "items.xlsx")
    assert is_valid is True
    assert doc_type == "excel"

    # Corrupted header
    corrupt_content = b"NOT_A_ZIP"
    is_valid, msg, doc_type = validate_document_content(corrupt_content, "items.xlsx")
    assert is_valid is False
    assert "not a valid Excel" in msg

def test_validate_document_content_csv():
    """Verify CSV validation."""
    csv_bytes = b"ItemCode,ItemName,InventoryItem\nITM001,Laptop,Yes\n"
    is_valid, msg, doc_type = validate_document_content(csv_bytes, "items.csv")
    assert is_valid is True
    assert doc_type == "excel"

@pytest.mark.asyncio
async def test_excel_item_extraction_consensus():
    """Verify 3-way extraction consensus on sample item Excel workbook."""
    sample_path = Path(__file__).resolve().parent.parent / "uploads" / "sample_item.xlsx"
    if not sample_path.exists():
        pytest.skip("sample_item.xlsx not present")

    extractions = await extraction_service.extract_all(str(sample_path))
    assert len(extractions) == 3

    methods = [e.method for e in extractions]
    assert "excel_grid" in methods
    assert "excel_table" in methods
    assert "excel_text_layout" in methods

    for ext in extractions:
        assert ext.success is True
        assert ext.master_type == MasterDataType.ITEM
        assert ext.data.get("ItemCode") == "ITM-90042"
        assert "Fastener" in ext.data.get("ItemName", "")
        assert ext.data.get("InventoryItem") is True

    # Check consensus comparison
    comparison = extraction_comparator.compare_extractions(extractions)
    assert comparison.status == ConflictStatus.AGREED
    assert comparison.overall_confidence == 1.0
    assert comparison.agreed_data["ItemCode"] == "ITM-90042"

    # Deterministic validation detects missing mandatory fields in legacy sample Excel
    val_res = validation_service.validate(MasterDataType.ITEM, comparison.agreed_data)
    assert val_res.valid is False
    missing_names = {m.field for m in val_res.missing_fields}
    assert "TaxRate" in missing_names
    assert "HSN" in missing_names

    # When mandatory fields are complemented, validation succeeds
    full_data = {
        **comparison.agreed_data,
        "TaxRate": 18.0,
        "ItemManagementMethod": "None",
        "ItemCategory": "Item",
        "MaterialType": "RM",
        "HSN": "73181500",
        "TaxCategory": "Taxable",
    }
    full_val = validation_service.validate(MasterDataType.ITEM, full_data)
    assert full_val.valid is True

@pytest.mark.asyncio
async def test_excel_bp_extraction_consensus():
    """Verify 3-way extraction consensus on sample business partner Excel."""
    sample_path = Path(__file__).resolve().parent.parent / "uploads" / "sample_supplier.xlsx"
    if not sample_path.exists():
        pytest.skip("sample_supplier.xlsx not present")

    extractions = await extraction_service.extract_all(str(sample_path))
    assert len(extractions) == 3

    comparison = extraction_comparator.compare_extractions(extractions)
    assert comparison.status == ConflictStatus.AGREED
    assert comparison.master_type == MasterDataType.BUSINESS_PARTNER
    assert comparison.agreed_data["CardCode"] == "V10048"
    assert comparison.agreed_data["CardType"] == "Supplier"

@pytest.mark.asyncio
async def test_excel_warehouse_extraction_consensus():
    """Verify 3-way extraction consensus on sample warehouse Excel."""
    sample_path = Path(__file__).resolve().parent.parent / "uploads" / "sample_warehouse.xlsx"
    if not sample_path.exists():
        pytest.skip("sample_warehouse.xlsx not present")

    extractions = await extraction_service.extract_all(str(sample_path))
    assert len(extractions) == 3

    comparison = extraction_comparator.compare_extractions(extractions)
    assert comparison.status == ConflictStatus.AGREED
    assert comparison.master_type == MasterDataType.WAREHOUSE
    assert comparison.agreed_data["WarehouseCode"] == "WH02"

def test_csv_upload_and_extraction(tmp_path):
    """Verify CSV upload through the HTTP API endpoint."""
    csv_file = tmp_path / "test_item.csv"
    csv_file.write_text(
        "Item Code,Item Name,Item Group,Inventory Item,Sales Item,Purchase Item,Inventory UOM,Tax Rate,Item Management Method,Item Category,Material Type,HSN,Tax Category\n"
        "ITM-CSV-01,High Precision Sensor,100,Yes,Yes,Yes,PCS,18%,None,Item,RM,73181500,Taxable\n",
        encoding="utf-8"
    )

    with open(csv_file, "rb") as f:
        res = client.post(
            "/api/documents/upload",
            files={"file": ("test_item.csv", f, "text/csv")},
            data={"master_type": "item"}
        )

    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["data"]["ItemCode"] == "ITM-CSV-01"
    assert data["data"]["status"] == "READY_FOR_CONFIRMATION"

def test_sample_excel_api_endpoint():
    """Verify sample excel download endpoint returns valid .xlsx content."""
    res = client.get("/api/documents/sample/item?format=excel")
    assert res.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in res.headers["content-type"]
    assert len(res.content) > 1000
    assert res.content.startswith(b"PK\x03\x04")
