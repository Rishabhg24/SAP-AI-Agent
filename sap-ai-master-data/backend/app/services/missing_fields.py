"""
Missing Field Engine for identifying mandatory SAP fields.
Returns user-friendly labels, business explanations, and sample formats.
"""
from typing import Any, Dict, List, Optional
from app.models.extraction import MasterDataType
from app.models.validation import MissingFieldInfo

MANDATORY_FIELD_DEFINITIONS = {
    MasterDataType.ITEM: [
        MissingFieldInfo(
            field="ItemCode",
            label="Item Code",
            reason="Required by SAP to uniquely identify the inventory item.",
            example="ITM-10024"
        ),
        MissingFieldInfo(
            field="ItemName",
            label="Item Description",
            reason="Required by SAP for cataloging, sales orders, and purchase orders.",
            example="Stainless Steel Hex Bolt M8x40"
        ),
        MissingFieldInfo(
            field="ItemsGroupCode",
            label="Item Group",
            reason="Classification group required for GL account determination.",
            example="100"
        ),
        MissingFieldInfo(
            field="InventoryUOM",
            label="Unit of Measure",
            reason="Base unit of measure for inventory management.",
            example="PCS"
        ),
        MissingFieldInfo(
            field="ItemType",
            label="Item Type",
            reason="Defines item behavior across Sales, Purchasing, and Inventory.",
            example="Inventory/Sales/Purchase"
        ),
        MissingFieldInfo(
            field="TaxRate",
            label="Tax Rate",
            reason="GST / VAT rate applied to item transactions.",
            example="18%"
        ),
        MissingFieldInfo(
            field="ItemManagementMethod",
            label="Management Method",
            reason="Inventory tracking method: Batch, Serial, or None.",
            example="Batch"
        ),
        MissingFieldInfo(
            field="ItemCategory",
            label="Item Category",
            reason="High-level category for SAP reporting and valuation.",
            example="Item"
        ),
        MissingFieldInfo(
            field="MaterialType",
            label="Material Type",
            reason="Material classification: Raw Material (RM), Finished Good (FG), etc.",
            example="RM"
        ),
        MissingFieldInfo(
            field="HSN",
            label="HSN / SAC Code",
            reason="Mandatory 6-8 digit Harmonized System of Nomenclature code for Indian GST compliance.",
            example="73181500"
        ),
        MissingFieldInfo(
            field="TaxCategory",
            label="Tax Category",
            reason="Taxability status: Taxable, Nil Rated, or Exempt.",
            example="Taxable"
        ),
    ],
    MasterDataType.BUSINESS_PARTNER: [
        MissingFieldInfo(
            field="CardCode",
            label="BP Code",
            reason="Required unique account code in SAP (max 15 chars).",
            example="V10024"
        ),
        MissingFieldInfo(
            field="CardName",
            label="BP Name",
            reason="Official legal entity name required on all financial and purchasing documents.",
            example="Apex Precision Components Ltd"
        ),
        MissingFieldInfo(
            field="Address",
            label="Registered Address",
            reason="Primary billing / registered street address.",
            example="Plot 42, Industrial Area Phase 2"
        ),
        MissingFieldInfo(
            field="TaxDetails",
            label="Tax Details",
            reason="Default tax structure applicable to the business partner.",
            example="GST 18%"
        ),
        MissingFieldInfo(
            field="PaymentTerms",
            label="Payment Terms",
            reason="Credit terms agreed for invoices and payables.",
            example="Net 30"
        ),
        MissingFieldInfo(
            field="Currency",
            label="Currency",
            reason="Account currency code (e.g. INR, USD, EUR).",
            example="INR"
        ),
        MissingFieldInfo(
            field="ControlAccount",
            label="GL Control Account",
            reason="Reconciliation account in General Ledger for AR/AP balances.",
            example="211000"
        ),
        MissingFieldInfo(
            field="GSTNo",
            label="GSTIN",
            reason="15-character Goods and Services Tax Identification Number.",
            example="27AABCU9603R1ZM"
        ),
        MissingFieldInfo(
            field="PANNo",
            label="PAN Number",
            reason="10-character Permanent Account Number for Indian tax reporting.",
            example="AABCU9603R"
        ),
    ],
    MasterDataType.WAREHOUSE: [
        MissingFieldInfo(
            field="WarehouseCode",
            label="Warehouse Code",
            reason="Unique identifier for the storage location in SAP (max 8 chars).",
            example="WH01"
        ),
        MissingFieldInfo(
            field="WarehouseName",
            label="Warehouse Name",
            reason="Descriptive name of the warehouse facility.",
            example="Central Distribution Depot"
        ),
        MissingFieldInfo(
            field="Location",
            label="Location Code",
            reason="Physical location reference code in SAP.",
            example="1"
        ),
        MissingFieldInfo(
            field="Address",
            label="Facility Address",
            reason="Physical street address of the warehouse facility.",
            example="100 Logistics Way, Industrial Park"
        ),
    ]
}

# Alias dictionary mapping canonical field names to acceptable alternate keys
FIELD_ALIASES = {
    # Item
    "ItemCode": ["ItemCode", "Item_Code", "ItemNo", "Item_No", "PartNumber", "PartNo", "Part No.", "Part No", "New Part No", "NEW PART NO", "SKU", "Code", "Item Code", "Item_Code"],
    "ItemName": ["ItemName", "Item_Name", "Description", "ItemDescription", "Item Description", "Name", "Item Name", "Master Item Name"],
    "ItemsGroupCode": ["ItemsGroupCode", "ItemGroup", "ItemsGroup", "Item_Group", "GroupCode", "ItemsGroup_Code", "Group"],
    "InventoryUOM": ["InventoryUOM", "UoM", "UOM", "UnitOfMeasure", "BaseUOM", "InvntryUom", "InventoryUOM "],
    "ItemType": ["ItemType", "Item_Type", "Type"],
    "TaxRate": ["TaxRate", "Tax_Rate", "TaxPercent", "TaxPercentage", "VatRate", "Tax"],
    "ItemManagementMethod": ["ItemManagementMethod", "ManagementMethod", "ManageMethod", "ItemManagement", "Method"],
    "ItemCategory": ["ItemCategory", "Item_Category", "Category", "ItemClass"],
    "MaterialType": ["MaterialType", "Material_Type", "MatType", "Material_Category"],
    "HSN": ["HSN", "HSNCode", "HSN_Code", "SAC", "SACCode", "ChapterID", "HSN Code"],
    "TaxCategory": ["TaxCategory", "Tax_Category", "VatCategory", "TaxType"],
    # Business Partner
    "CardCode": ["CardCode", "Card_Code", "BPCode", "BPcode", "CustomerCode", "VendorCode", "PartnerCode", "Code", "BP Code", "Vendor Code", "Customer Code", "Customer ID", "CustomerID", "Customer_ID", "Vendor ID", "VendorID", "Party Code"],
    "CardName": ["CardName", "Card_Name", "Name", "BPName", "BPname", "CustomerName", "VendorName", "CompanyName", "BP Name", "Vendor Name", "Customer Name", "Company", "Company Name", "Full Name"],
    "CardType": ["CardType", "Card_Type", "BPType", "BP_Type", "BP- Type", "BP - Type", "Type", "PartnerType", "BP Type", "GroupType", "Card_Type", "Vendor Type", "Customer Type"],
    "Address": ["Address", "Street", "BillingAddress", "RegisteredAddress", "FacilityAddress", "Bill to Building", "Address 1"],
    "TaxDetails": ["TaxDetails", "Tax_Details", "TaxCode", "VatGroup", "TaxStructure"],
    "PaymentTerms": ["PaymentTerms", "Payment_Terms", "PayTermsGrpCode", "Terms", "PaymentTerm"],
    "Currency": ["Currency", "Curr", "DocCurrency", "BP Currency"],
    "ControlAccount": ["ControlAccount", "Control_Account", "DebitorAccount", "CreditorAccount", "GLAccount", "AccountCode", "GL"],
    "GSTNo": ["GSTNo", "GST_No", "GSTIN", "FederalTaxID", "TaxId1", "LicTradNum", "GSTN  No.", "GSTN No.", "Bill GSTIN"],
    "PANNo": ["PANNo", "PAN_No", "PAN", "TaxId0", "PanNumber", "P.A.N. No", "P.A.N. No."],
    "Phone1": ["Phone1", "Phone", "Mobile Phone", "Telephone1", "Phone 1"],
    "EmailAddress": ["EmailAddress", "Email", "E-Mail", "Email Address"],
    # Warehouse
    "WarehouseCode": ["WarehouseCode", "Warehouse_Code", "WhsCode", "WHCode", "StorageCode", "Code", "Warehouse Code", "WH Code", "Whs Code", "Warehouse"],
    "WarehouseName": ["WarehouseName", "Warehouse_Name", "WhsName", "WHName", "FacilityName", "Warehouse Name", "Whs Name", "WH Name"],
    "Location": ["Location", "LocationCode", "LocationId", "OLCT", "Default Location"],
}

class MissingFieldEngine:
    @staticmethod
    def get_field_value_with_aliases(field: str, data: Dict[str, Any]) -> Any:
        """Retrieve value using canonical name or any known aliases."""
        if field in data and data[field] is not None and str(data[field]).strip() != "":
            return data[field]
        aliases = FIELD_ALIASES.get(field, [])
        for alias in aliases:
            if alias in data and data[alias] is not None and str(data[alias]).strip() != "":
                return data[alias]
            # Case-insensitive check
            for k, v in data.items():
                if k.lower() == alias.lower() and v is not None and str(v).strip() != "":
                    return v
        return None

    @classmethod
    def identify_missing_fields(cls, master_type: MasterDataType, data: Dict[str, Any]) -> List[MissingFieldInfo]:
        """Check provided data against mandatory schema for the master data type."""
        definitions = MANDATORY_FIELD_DEFINITIONS.get(master_type, [])
        missing: List[MissingFieldInfo] = []

        for req in definitions:
            val = cls.get_field_value_with_aliases(req.field, data)

            # Special case for ItemType: if operational boolean flags are explicitly set (e.g. InventoryItem=True)
            if req.field == "ItemType" and (val is None or (isinstance(val, str) and not val.strip())):
                if any(flag in data for flag in ["InventoryItem", "SalesItem", "PurchaseItem"]):
                    continue

            # Special case for ItemManagementMethod: if ManageSerialNumbers or ManageBatchNumbers is set
            if req.field == "ItemManagementMethod" and (val is None or (isinstance(val, str) and not val.strip())):
                if "ManageSerialNumbers" in data or "ManageBatchNumbers" in data:
                    continue

            # Special case for GSTNo: only mandatory if party is registered
            if req.field == "GSTNo":
                # Check if party is marked as Unregistered
                reg_status = str(data.get("GSTRegStatus") or data.get("RegistrationStatus") or "").strip().lower()
                raw_gst = str(val or "").strip().upper()
                if reg_status in ["unregistered", "urp", "no", "composition"] or raw_gst in ["UNREGISTERED", "URP", "N/A", "NA"]:
                    continue

            # Special case for PANNo: can be derived from 15-character GSTIN (chars 3 to 12)
            if req.field == "PANNo" and (val is None or (isinstance(val, str) and not val.strip())):
                gst_val = str(cls.get_field_value_with_aliases("GSTNo", data) or "").strip().upper()
                if len(gst_val) == 15 and gst_val[:2].isdigit() and gst_val[2:12].isalnum():
                    # PAN is present in GSTIN
                    continue

            if val is None or (isinstance(val, str) and not str(val).strip()):
                missing.append(req)

        return missing

missing_field_engine = MissingFieldEngine()
