"""
Authoritative SAP Business One field mappings, dictionary aliases,
typo tolerance, and deterministic field validation rules.
"""
import difflib
import re
from typing import Any, Dict, Optional, Tuple

# Authoritative Field Mappings to SAP Business One Service Layer properties
BP_FIELD_MAPPINGS: Dict[str, str] = {
    # CardCode
    "cardcode": "CardCode",
    "card code": "CardCode",
    "code": "CardCode",
    "customer code": "CardCode",
    "vendor code": "CardCode",
    "bp code": "CardCode",
    "partner code": "CardCode",
    "business partner code": "CardCode",

    # CardName
    "cardname": "CardName",
    "customer name": "CardName",
    "customername": "CardName",
    "vendor name": "CardName",
    "vendorname": "CardName",
    "supplier name": "CardName",
    "suppliername": "CardName",
    "bp name": "CardName",
    "bpname": "CardName",
    "partner name": "CardName",
    "partnername": "CardName",
    "card name": "CardName",
    "name": "CardName",
    "company": "CardName",
    "company name": "CardName",
    "business partner": "CardName",
    "business partner name": "CardName",
    "partner": "CardName",

    # FederalTaxID / GST / VAT / PAN
    "federaltaxid": "FederalTaxID",
    "federal tax id": "FederalTaxID",
    "tax id": "FederalTaxID",
    "taxid": "FederalTaxID",
    "tax": "TaxDetails",
    "tax_id": "FederalTaxID",
    "gst": "GSTNo",
    "gstin": "GSTNo",
    "gst no": "GSTNo",
    "gst number": "GSTNo",
    "gstno": "GSTNo",
    "pan": "PANNo",
    "panno": "PANNo",
    "pan no": "PANNo",
    "pan number": "PANNo",
    "vat": "FederalTaxID",
    "vat id": "FederalTaxID",
    "vat no": "FederalTaxID",
    "tin": "FederalTaxID",

    # Phone1
    "phone1": "Phone1",
    "phone": "Phone1",
    "phone number": "Phone1",
    "phonenumber": "Phone1",
    "mobile": "Phone1",
    "mobile number": "Phone1",
    "mobilenumber": "Phone1",
    "contact": "Phone1",
    "contact number": "Phone1",
    "telephone": "Phone1",
    "cell": "Phone1",

    # EmailAddress
    "emailaddress": "EmailAddress",
    "email": "EmailAddress",
    "email address": "EmailAddress",
    "email id": "EmailAddress",
    "mail": "EmailAddress",

    # CardType
    "cardtype": "CardType",
    "card type": "CardType",
    "type": "CardType",
    "partner type": "CardType",

    # Payment & Accounting
    "paymentterms": "PaymentTerms",
    "payment terms": "PaymentTerms",
    "pay terms": "PaymentTerms",
    "terms": "PaymentTerms",
    "currency": "Currency",
    "curr": "Currency",
    "controlaccount": "ControlAccount",
    "control account": "ControlAccount",
    "gl account": "ControlAccount",
    "taxdetails": "TaxDetails",
    "tax details": "TaxDetails",
    "tax structure": "TaxDetails",

    # Address & Location
    "address": "Address",
    "street address": "Address",
    "registered address": "Address",
    "street": "Address",
    "addres": "Address",
    "addes": "Address",
    "adres": "Address",
    "addrs": "Address",
    "addr": "Address",
    "location": "Address",
    "zipcode": "ZipCode",
    "zip code": "ZipCode",
    "zip": "ZipCode",
    "postal code": "ZipCode",
    "postalcode": "ZipCode",
    "pincode": "ZipCode",
    "pin": "ZipCode",
    "pincde": "ZipCode",
    "city": "City",
    "cirty": "City",
    "town": "City",
    "state": "State",
    "stat": "State",
    "country": "Country",
}

ITEM_FIELD_MAPPINGS: Dict[str, str] = {
    # ItemCode
    "itemcode": "ItemCode",
    "item code": "ItemCode",
    "code": "ItemCode",
    "sku": "ItemCode",
    "part number": "ItemCode",
    "part code": "ItemCode",
    "item no": "ItemCode",
    "itemno": "ItemCode",

    # ItemName
    "itemname": "ItemName",
    "item name": "ItemName",
    "name": "ItemName",
    "description": "ItemName",
    "item description": "ItemName",
    "product name": "ItemName",
    "productname": "ItemName",
    "title": "ItemName",

    # ItemsGroupCode
    "itemsgroupcode": "ItemsGroupCode",
    "item group code": "ItemsGroupCode",
    "item group": "ItemsGroupCode",
    "group code": "ItemsGroupCode",
    "groupcode": "ItemsGroupCode",
    "group": "ItemsGroupCode",
    "category": "ItemsGroupCode",
    "category code": "ItemsGroupCode",

    # Classification & Tax
    "inventoryuom": "InventoryUOM",
    "inventory uom": "InventoryUOM",
    "uom": "InventoryUOM",
    "unit": "InventoryUOM",
    "unit of measure": "InventoryUOM",
    "itemtype": "ItemType",
    "item type": "ItemType",
    "taxrate": "TaxRate",
    "tax rate": "TaxRate",
    "tax": "TaxRate",
    "hsn": "HSN",
    "hsn code": "HSN",
    "sac": "HSN",
    "sac code": "HSN",
    "price": "Price",
    "standard price": "Price",
    "unit price": "Price",
    "materialtype": "MaterialType",
    "material type": "MaterialType",
    "itemmanagementmethod": "ItemManagementMethod",
    "management method": "ItemManagementMethod",
    "itemcategory": "ItemCategory",
    "item category": "ItemCategory",
    "taxcategory": "TaxCategory",
    "tax category": "TaxCategory",

    # Units & Flags
    "salesunit": "SalesUnit",
    "sales unit": "SalesUnit",
    "purchaseunit": "PurchaseUnit",
    "purchase unit": "PurchaseUnit",
    "barcode": "BarCode",
    "bar code": "BarCode",
    "inventoryitem": "InventoryItem",
    "salesitem": "SalesItem",
    "purchaseitem": "PurchaseItem",
}

WAREHOUSE_FIELD_MAPPINGS: Dict[str, str] = {
    # WarehouseCode
    "warehousecode": "WarehouseCode",
    "warehouse code": "WarehouseCode",
    "wh code": "WarehouseCode",
    "whs code": "WarehouseCode",
    "whse code": "WarehouseCode",
    "code": "WarehouseCode",

    # WarehouseName
    "warehousename": "WarehouseName",
    "warehouse name": "WarehouseName",
    "wh name": "WarehouseName",
    "whse name": "WarehouseName",
    "name": "WarehouseName",

    # Location & Address
    "location": "Location",
    "location code": "Location",
    "address": "Address",
    "street": "Address",
    "street address": "Address",
    "addres": "Address",
    "addes": "Address",
    "adres": "Address",
    "addrs": "Address",
    "city": "City",
    "cirty": "City",
    "town": "City",
    "state": "State",
    "country": "Country",
    "zipcode": "ZipCode",

    # Status
    "inactive": "Inactive",
    "status": "Inactive",
    "binactivat": "BinActivat",
    "enable bin": "BinActivat",
}

# Authoritative Mandatory Fields and Specifications for Master Data Creation
MANDATORY_CREATION_SCHEMA: Dict[str, Dict[str, Dict[str, Any]]] = {
    "BusinessPartners": {
        "CardCode": {"label": "Customer / Vendor Code (CardCode)", "max_length": 15, "example": "CV24 / C20099 / V10099", "mandatory": True, "reason": "Unique primary key in SAP (max 15 characters)"},
        "CardName": {"label": "Business Partner Name (CardName)", "max_length": 100, "example": "Cinntra Global Logistics Ltd", "mandatory": True, "reason": "Official legal entity name required on all SAP invoices"},
        "CardType": {"label": "Business Partner Type (CardType)", "example": "Customer / Vendor", "mandatory": True, "reason": "Classification as Customer (cCustomer) or Supplier (cSupplier)"},
        "Phone1": {"label": "Phone Number", "example": "9876543210", "mandatory": False, "reason": "Primary contact phone number"},
        "Address": {"label": "Registered Address", "example": "Plot 42, Cyber City, Mumbai", "mandatory": False, "reason": "Registered street or billing address for correspondence"},
        "GSTNo": {"label": "GST Number (GSTIN)", "example": "27AABCU9603R1ZM", "mandatory": False, "reason": "15-digit GSTIN (or 'UNREGISTERED' for unregistered parties)"},
        "PANNo": {"label": "Permanent Account Number (PAN)", "example": "AABCU9603R", "mandatory": False, "reason": "10-digit PAN (auto-derived from GSTIN)"},
        "TaxDetails": {"label": "Tax Details / Structure", "example": "GST 18%", "default": "GST 18%", "mandatory": False, "reason": "Applicable tax rate group"},
        "PaymentTerms": {"label": "Payment Terms", "example": "Net 30", "default": 30, "mandatory": False, "reason": "Payment schedule (e.g. Net 30)"},
        "Currency": {"label": "Currency", "example": "INR", "default": "INR", "mandatory": False, "reason": "Default document currency"},
        "ControlAccount": {"label": "Control Account", "example": "123000", "default": "123000", "mandatory": False, "reason": "General ledger balance consolidation account"},
    },
    "Items": {
        "ItemCode": {"label": "Item Code / SKU", "max_length": 50, "example": "ITM-9901", "mandatory": True, "reason": "Unique inventory identifier in SAP (max 50 chars)"},
        "ItemName": {"label": "Item Name / Description", "max_length": 100, "example": "Stainless Steel Hex Bolt M8", "mandatory": True, "reason": "Item catalog description for sales & purchase orders"},
        "InventoryUOM": {"label": "Unit of Measure (UoM)", "example": "PCS", "default": "PCS", "mandatory": False, "reason": "Base inventory unit of measure (PCS, BOX, KG, MTR)"},
        "ItemsGroupCode": {"label": "Item Group Code", "example": "100", "default": 100, "mandatory": False, "reason": "Item group code (OITB) for GL account determination"},
        "TaxRate": {"label": "Tax Rate (%)", "example": "18", "default": "18%", "mandatory": False, "reason": "Applicable GST/VAT tax percentage in SAP"},
        "ItemType": {"label": "Item Type", "example": "Inventory", "default": "Inventory", "mandatory": False, "reason": "Operational classification (Inventory/Sales/Purchase)"},
        "ItemManagementMethod": {"label": "Management Method", "example": "None", "default": "None", "mandatory": False, "reason": "Tracking method: None, Serial, or Batch"},
        "ItemCategory": {"label": "Item Category", "example": "Item", "default": "Item", "mandatory": False, "reason": "Tangible Item or Service"},
        "MaterialType": {"label": "Material Type", "example": "RM", "default": "RM", "mandatory": False, "reason": "Classification: RM (Raw Material), FG (Finished Goods), Capital Goods"},
        "HSN": {"label": "HSN / SAC Code", "example": "73181500", "default": "73181500", "mandatory": False, "reason": "Harmonized System of Nomenclature code for GST compliance"},
        "TaxCategory": {"label": "Tax Category", "example": "Standard", "default": "Standard", "mandatory": False, "reason": "Tax category under statutory regulations"},
    },
    "Warehouses": {
        "WarehouseCode": {"label": "Warehouse Code", "max_length": 8, "example": "WH09", "mandatory": True, "reason": "Unique storage location code in SAP (max 8 chars)"},
        "WarehouseName": {"label": "Warehouse Name", "max_length": 100, "example": "North Logistics Hub", "mandatory": False, "reason": "Descriptive title of the warehouse facility"},
        "Address": {"label": "Warehouse Physical Address", "example": "100 Logistics Way, Industrial Park", "mandatory": False, "reason": "Physical street address where goods are stored"},
        "Location": {"label": "Location Code", "example": "1", "default": 1, "mandatory": False, "reason": "Physical location ID or jurisdiction (OLCT)"},
    }
}


def normalize_field_name(entity: str, raw_field: str) -> Optional[str]:
    """Normalize natural language field names into authoritative SAP Service Layer property with typo tolerance."""
    if not raw_field:
        return None
    clean = raw_field.strip().lower().replace("_", " ").replace("-", " ")
    clean = re.sub(r"^(?:the\s+|of\s+|for\s+)", "", clean).strip()
    clean = re.sub(r"\s+", " ", clean)

    mapping: Dict[str, str] = {}
    if entity == "BusinessPartners":
        mapping = BP_FIELD_MAPPINGS
    elif entity == "Items":
        mapping = ITEM_FIELD_MAPPINGS
    elif entity == "Warehouses":
        mapping = WAREHOUSE_FIELD_MAPPINGS
    else:
        mapping = {**BP_FIELD_MAPPINGS, **ITEM_FIELD_MAPPINGS, **WAREHOUSE_FIELD_MAPPINGS}

    if clean in mapping:
        return mapping[clean]
    clean_nospace = clean.replace(" ", "")
    if clean_nospace in mapping:
        return mapping[clean_nospace]

    # Fuzzy matching for minor spelling mistakes (e.g. 'addes' -> 'Address', 'cirty' -> 'City')
    matches = difflib.get_close_matches(clean, mapping.keys(), n=1, cutoff=0.72)
    if matches:
        return mapping[matches[0]]

    matches_nospace = difflib.get_close_matches(clean_nospace, mapping.keys(), n=1, cutoff=0.72)
    if matches_nospace:
        return mapping[matches_nospace[0]]

    return None


def validate_field_value(entity: str, field_name: str, value: Any) -> Tuple[bool, Any, Optional[str]]:
    """
    Deterministically validate and normalize an individual field value.
    Returns (is_valid, normalized_val, error_message).
    """
    val_str = str(value).strip()
    if not val_str:
        return False, None, f"{field_name} cannot be empty."

    if entity == "BusinessPartners":
        if field_name == "CardCode":
            # If value contains spaces or word 'and', it cannot be a single CardCode
            if " " in val_str or re.search(r"\band\b", val_str, re.IGNORECASE):
                return False, None, "CardCode must be a single alphanumeric code without spaces."
            cleaned_code = re.sub(r"[^A-Za-z0-9_-]", "", val_str).upper()
            if not cleaned_code or cleaned_code in ["AND", "THE", "IS", "NEW", "BP", "CODE"]:
                return False, None, "CardCode must contain valid alphanumeric characters."
            # Guard against accidental concatenation like CV02ANDABC or CV24ANDABC
            if re.search(r"^(?:CV|BP|C|V|L)\d{1,8}AND[A-Z0-9]+$", cleaned_code):
                return False, None, f"CardCode '{cleaned_code}' appears to be a merged code and name. Please provide code separately."
            if len(cleaned_code) > 15:
                return False, None, f"CardCode exceeds maximum length of 15 characters (provided {len(cleaned_code)})."
            return True, cleaned_code, None

        if field_name == "CardName":
            cleaned_name = re.sub(r"\s+(?:business\s*partner|partner|customer|vendor|supplier)$", "", val_str, flags=re.IGNORECASE).strip()
            cleaned_name = re.sub(r"^(?:called|named|is|a|an|the)\s+", "", cleaned_name, flags=re.IGNORECASE).strip()
            if not cleaned_name:
                cleaned_name = val_str
            return True, cleaned_name[:100], None

        if field_name == "CardType":
            clean_type = val_str.lower().strip()
            if any(k in clean_type for k in ["sup", "ven"]):
                return True, "cSupplier", None
            if any(k in clean_type for k in ["lid", "lead"]):
                return True, "cLid", None
            if any(k in clean_type for k in ["cust", "client"]):
                return True, "cCustomer", None
            if clean_type in ["customer", "c", "cust"]:
                return True, "cCustomer", None
            if clean_type in ["vendor", "supplier", "v", "supp"]:
                return True, "cSupplier", None
            return False, None, f"Invalid Business Partner Type '{val_str}'. Please specify Customer or Vendor."

        if field_name == "Phone1":
            cleaned_phone = re.sub(r"[^\d+]", "", val_str)
            if not cleaned_phone:
                return True, val_str[:50], None
            return True, cleaned_phone[:50], None

        if field_name == "GSTNo":
            clean_gst = val_str.upper().replace(" ", "").replace("-", "")
            if clean_gst in ["UNREGISTERED", "URP", "N/A", "NA", "NONE"]:
                return True, "UNREGISTERED", None
            gst_regex = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
            if not re.match(gst_regex, clean_gst):
                return False, None, (
                    f"Invalid GSTIN format '{val_str}'. Standard GSTIN must be 15 alphanumeric characters "
                    "(e.g. 27AABCU9603R1ZM). If party is unregistered, reply 'UNREGISTERED'."
                )
            return True, clean_gst, None

        if field_name == "PANNo":
            clean_pan = val_str.upper().replace(" ", "").replace("-", "")
            pan_regex = r"^[A-Z]{5}\d{4}[A-Z]{1}$"
            if not re.match(pan_regex, clean_pan):
                return False, None, (
                    f"Invalid PAN format '{val_str}'. Permanent Account Number must be exactly 10 alphanumeric characters "
                    "(e.g. AABCU9603R)."
                )
            return True, clean_pan, None

        if field_name == "PaymentTerms":
            num_match = re.search(r"\d+", val_str)
            if num_match:
                return True, int(num_match.group(0)), None
            return True, 30, None

    elif entity == "Items":
        if field_name == "ItemCode":
            cleaned_code = re.sub(r"[^A-Za-z0-9_-]", "", val_str).upper()
            if not cleaned_code:
                return False, None, "ItemCode must contain alphanumeric characters."
            if len(cleaned_code) > 50:
                return False, None, f"ItemCode exceeds maximum length of 50 characters (provided {len(cleaned_code)})."
            return True, cleaned_code, None

        if field_name == "TaxRate":
            clean_rate = re.sub(r"[^\d.]", "", val_str)
            if not clean_rate:
                return False, None, "TaxRate must be numeric (e.g. 18%)."
            return True, f"{clean_rate}%", None

        if field_name == "ItemsGroupCode":
            num_match = re.search(r"\d+", val_str)
            if num_match:
                return True, int(num_match.group(0)), None
            return True, 100, None

        if field_name == "ItemManagementMethod":
            clean_m = val_str.lower()
            if "serial" in clean_m:
                return True, "Serial", None
            if "batch" in clean_m:
                return True, "Batch", None
            return True, "None", None

    elif entity == "Warehouses":
        if field_name == "WarehouseCode":
            cleaned_code = re.sub(r"[^A-Za-z0-9_-]", "", val_str).upper()
            if not cleaned_code:
                return False, None, "WarehouseCode must contain alphanumeric characters."
            if len(cleaned_code) > 8:
                return False, None, f"WarehouseCode exceeds maximum length of 8 characters (provided {len(cleaned_code)})."
            return True, cleaned_code, None

        if field_name == "Location":
            num_match = re.search(r"\d+", val_str)
            if num_match:
                return True, int(num_match.group(0)), None
            return True, 1, None

    return True, val_str, None
