import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.extraction import MasterDataType
from app.services.chat_service import nvidia_chat_service

client = TestClient(app)

@pytest.mark.asyncio
async def test_dynamic_nemotron_document_transformation():
    # Test Nemotron structured parser
    sample_text = """
    Vendor Ingestion Sheet:
    Supplier Code: V99901
    Supplier Name: Techtronix Semiconductors India Ltd
    GSTIN: 27AAACT1234F1Z1
    Phone: +91-9876543210
    Email: supplies@techtronix.in
    Address: 45 MIDC Industrial Area, Pune, MH, 411018
    """
    
    # Mock LLM response
    mock_llm_payload = {
        "master_type": "business_partner",
        "records": [
            {
                "CardCode": "V99901",
                "CardName": "Techtronix Semiconductors India Ltd",
                "CardType": "cSupplier",
                "FederalTaxID": "27AAACT1234F1Z1",
                "Phone1": "+91-9876543210",
                "EmailAddress": "supplies@techtronix.in",
                "Address": "45 MIDC Industrial Area",
                "City": "Pune",
                "State": "MH",
                "ZipCode": "411018",
                "Country": "IN"
            }
        ],
        "confidence": 0.98,
        "summary": "Extracted 1 supplier record"
    }

    with patch.object(nvidia_chat_service, "generate", new_callable=AsyncMock) as mock_gen:
        import json
        mock_gen.return_value = json.dumps(mock_llm_payload)
        
        res = await nvidia_chat_service.transform_document_to_sap_records(sample_text, preferred_entity="business_partner")
        
        assert res["master_type"] == "business_partner"
        assert len(res["records"]) == 1
        assert res["records"][0]["CardCode"] == "V99901"
        assert res["records"][0]["CardType"] == "cSupplier"
        assert res["records"][0]["FederalTaxID"] == "27AAACT1234F1Z1"

def test_upload_endpoint_ai_flow():
    csv_content = b"CustomHeader1,CustomHeader2\nUnknown1,Unknown2\n"
    files = {"file": ("unstructured_data.csv", csv_content, "text/csv")}
    
    mock_llm_payload = {
        "master_type": "business_partner",
        "records": [
            {
                "CardCode": "C55001",
                "CardName": "AI Discovered Client Ltd",
                "CardType": "cCustomer",
                "FederalTaxID": "29ABCDE1234F1Z5",
                "Phone1": "9876543210",
                "EmailAddress": "client@discovered.com",
                "Address": "MG Road",
                "City": "Bangalore",
                "State": "KA",
                "ZipCode": "560001",
                "Country": "IN"
            }
        ],
        "confidence": 0.95
    }

    with patch.object(nvidia_chat_service, "transform_document_to_sap_records", new_callable=AsyncMock) as mock_transform:
        mock_transform.return_value = mock_llm_payload
        
        response = client.post(
            "/api/documents/upload",
            files=files,
            data={"master_type": "business_partner", "use_ai": "true"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["ai_enhanced"] is True
        assert len(data["data"]["extracted_records"]) == 1
        assert data["data"]["extracted_records"][0]["CardCode"] == "C55001"
