"""
Unit tests for multi-engine extraction comparison and conflict detection.
"""
import pytest
from app.models.extraction import (
    ConflictStatus,
    MasterDataType,
    SingleExtractorOutput
)
from app.services.extraction_compare import extraction_comparator

def test_consensus_agreement():
    """All 3 extractors agree on all fields."""
    out1 = SingleExtractorOutput(
        method="pymupdf",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITM001", "ItemName": "Sample Item", "InventoryItem": True}
    )
    out2 = SingleExtractorOutput(
        method="pdfplumber",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITM001", "ItemName": "Sample Item", "InventoryItem": True}
    )
    out3 = SingleExtractorOutput(
        method="ocr_layout",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITM001", "ItemName": "Sample Item", "InventoryItem": True}
    )

    res = extraction_comparator.compare_extractions([out1, out2, out3])
    assert res.status == ConflictStatus.AGREED
    assert res.overall_confidence == 1.0
    assert len(res.conflicts) == 0
    assert res.agreed_data["ItemCode"] == "ITM001"
    assert res.agreed_data["ItemName"] == "Sample Item"

def test_conflict_detection():
    """Extractors disagree on ItemCode."""
    out1 = SingleExtractorOutput(
        method="pymupdf",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITEM001", "ItemName": "Sample Item"}
    )
    out2 = SingleExtractorOutput(
        method="pdfplumber",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITEM001", "ItemName": "Sample Item"}
    )
    out3 = SingleExtractorOutput(
        method="ocr_layout",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITEM002", "ItemName": "Sample Item"}
    )

    res = extraction_comparator.compare_extractions([out1, out2, out3])
    assert res.status == ConflictStatus.CONFLICT
    assert len(res.conflicts) == 1
    conflict_field = res.conflicts[0]
    assert conflict_field.field_name == "ItemCode"
    assert "ITEM001" in conflict_field.distinct_values
    assert "ITEM002" in conflict_field.distinct_values

def test_conflict_resolution_with_user_input():
    """User provides manual correction for a conflicting field."""
    out1 = SingleExtractorOutput(
        method="pymupdf",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITEM001"}
    )
    out2 = SingleExtractorOutput(
        method="pdfplumber",
        master_type=MasterDataType.ITEM,
        data={"ItemCode": "ITEM002"}
    )

    # First check conflict exists
    res_before = extraction_comparator.compare_extractions([out1, out2])
    assert res_before.status == ConflictStatus.CONFLICT

    # Resolve with user selection
    res_after = extraction_comparator.compare_extractions(
        [out1, out2],
        user_corrections={"ItemCode": "ITEM001"}
    )
    assert res_after.status == ConflictStatus.AGREED
    assert res_after.agreed_data["ItemCode"] == "ITEM001"
