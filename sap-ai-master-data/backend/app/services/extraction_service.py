"""
Multi-engine document extraction service for PDF and Excel/CSV spreadsheets.
Executes 3 independent extraction methods for consensus verification:
For PDFs:
- Method 1: PyMuPDF (fitz) text block extraction
- Method 2: pdfplumber tabular and word extraction
- Method 3: OCR / rendered image layout fallback
For Excel & CSV:
- Method 1: Excel Grid & Key-Value cell scanner (openpyxl/csv)
- Method 2: Excel Tabular Header & Row mapper
- Method 3: Excel Serialized Text Layout pattern stream

AI-Driven Header Mapping (added):
Each Excel extraction method first attempts to send raw column headers to the
NVIDIA Nemotron LLM via get_ai_column_mapping() to obtain a JSON
{ExcelHeader -> SAPField} dict. If the AI call succeeds, parse_spreadsheet_data_with_mapping()
maps data rows using the AI-resolved column indices. If the AI is unavailable,
times out, or returns invalid JSON, the original regex-based parse_spreadsheet_data()
is used as a transparent fallback — preserving full backward compatibility.

Dynamic/Unstructured Column Mapping (extended):
Handles real-world vendor/customer/item master sheets with aliased, abbreviated,
misspelled, or domain-specific column headers such as:
  - "Partycode", "PartyNmae", "BState", "GSTN No.", "Bill Building",
    "Ship to Building", "Bill-ZipCode", "Vendor Account", "GST Type", etc.
"""
import asyncio
import csv
import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
import openpyxl
import pdfplumber
from PIL import Image

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

from app.models.extraction import MasterDataType, SingleExtractorOutput
from app.services.normalization_service import normalization_service
from app.utils.logging import logger

# ---------------------------------------------------------------------------
# Master data field aliases for regex matching (KEPT — used as fallback)
# ---------------------------------------------------------------------------

ITEM_FIELD_PATTERNS = {
    "ItemCode": [
        r"item\s*code\b", r"item\s*no\.?", r"item\s*num(?:ber)?\b", r"itemcode\b",
        r"part\s*number\b", r"part\s*no\.?", r"sku\b", r"product\s*code\b",
        r"material\s*no\.?", r"material\s*code\b", r"parentkey\b", r"recordkey\b",
        r"item\s*id\b", r"prod(?:uct)?\s*id\b", r"mat(?:erial)?\s*id\b",
        r"article\s*code\b", r"article\s*no\.?", r"component\s*code\b",
        r"goods\s*code\b", r"catalogue\s*no\.?", r"cat\s*no\.?",
    ],
    "ItemName": [
        r"item\s*name\b", r"itemname\b", r"item\s*desc(?:ription)?\b",
        r"description\b", r"product\s*name\b", r"material\s*description\b",
        r"goods\s*name\b", r"article\s*name\b", r"component\s*name\b",
        r"prod(?:uct)?\s*desc(?:ription)?\b", r"item\s*title\b",
        r"stock\s*desc(?:ription)?\b", r"part\s*name\b",
    ],
    "ItemsGroupCode": [
        r"item\s*group\b", r"itemsgroupcode\b", r"itmsgrpcod\b", r"group\s*code\b",
        r"category\s*code\b", r"item\s*group\s*code\b", r"prod(?:uct)?\s*group\b",
        r"material\s*group\b", r"item\s*class(?:ification)?\b",
        r"product\s*category\b", r"goods\s*category\b",
    ],
    "InventoryItem": [
        r"inventory\s*item\b", r"invntitem\b", r"manage\s*stock\b",
        r"stock(?:ed)?\s*item\b", r"keep\s*stock\b", r"maintain\s*stock\b",
    ],
    "SalesItem": [
        r"sales\s*item\b", r"sellitem\b", r"sellable\b",
        r"can\s*sell\b", r"for\s*sale\b", r"sell(?:ing)?\s*item\b",
    ],
    "PurchaseItem": [
        r"purchase\s*item\b", r"prchseitem\b", r"purchasable\b",
        r"can\s*buy\b", r"for\s*purchase\b", r"buy(?:ing)?\s*item\b",
    ],
    "InventoryUOM": [
        r"inventory\s*uom\b", r"invntruom\b", r"base\s*uom\b",
        r"unit\s*of\s*measure\b", r"uom\b", r"base\s*unit\b",
        r"primary\s*uom\b", r"stock\s*uom\b", r"default\s*uom\b",
        r"unit\b",
    ],
    "ItemType": [
        r"item\s*type\b", r"itemtype\b", r"material\s*classification\b",
        r"goods\s*type\b", r"product\s*type\b", r"stock\s*type\b",
    ],
    "TaxRate": [
        r"tax\s*rate\b", r"tax\s*percent(?:age)?\b", r"vat\s*rate\b",
        r"gst\s*rate\b", r"taxrate\b", r"tax\s*%\b", r"vat\s*%\b",
        r"gst\s*%\b", r"duty\s*rate\b", r"cgst\s*rate\b", r"sgst\s*rate\b",
        r"igst\s*rate\b",
    ],
    "ItemManagementMethod": [
        r"item\s*management\s*method\b", r"management\s*method\b",
        r"manage\s*method\b", r"tracking\s*method\b", r"batch\s*or\s*serial\b",
        r"serial\s*\/\s*batch\b", r"manage\s*by\b",
    ],
    "ItemCategory": [
        r"item\s*category\b", r"itemcategory\b", r"item\s*class\b",
        r"itemclass\b", r"service\s*or\s*item\b", r"product\s*category\b",
        r"goods\s*class\b",
    ],
    "MaterialType": [
        r"material\s*type\b", r"materialtype\b", r"mattype\b",
        r"goods\s*type\b", r"stock\s*type\b",
    ],
    "HSN": [
        r"hsn\s*code\b", r"hsn\b", r"sac\s*code\b", r"sac\b",
        r"chapter\s*id\b", r"chapterid\b", r"hsn\s*\/\s*sac\b",
        r"tariff\s*code\b", r"hs\s*code\b",
    ],
    "TaxCategory": [
        r"tax\s*category\b", r"taxcategory\b", r"vat\s*category\b",
        r"tax\s*classification\b", r"gst\s*category\b",
    ],
    "SalesUnit": [
        r"sales\s*unit\b", r"sales\s*uom\b", r"salunit\b",
        r"selling\s*unit\b", r"sale\s*uom\b",
    ],
    "PurchaseUnit": [
        r"purchase\s*unit\b", r"purchase\s*uom\b", r"buyunit\b",
        r"buying\s*unit\b", r"procurement\s*uom\b",
    ],
    "BarCode": [
        r"bar\s*code\b", r"barcode\b", r"codebars\b", r"ean\b",
        r"upc\b", r"ean\s*13\b", r"ean\s*8\b", r"scan\s*code\b",
    ],
    "SalesUnitWeight": [
        r"sales\s*weight\b", r"unit\s*weight\b", r"gross\s*weight\b",
        r"weight\b", r"sweight\b", r"net\s*weight\b", r"item\s*weight\b",
    ],
    "LeadTime": [
        r"lead\s*time\b", r"leadtime\b", r"procurement\s*days\b",
        r"delivery\s*days\b", r"replenishment\s*time\b",
    ],
    "MinOrderQty": [
        r"min(?:imum)?\s*order\s*qty\b", r"moq\b", r"min\s*qty\b",
        r"minimum\s*quantity\b",
    ],
    "PriceList": [
        r"price\s*list\b", r"pricelist\b", r"list\s*price\b",
        r"sales\s*price\b", r"unit\s*price\b", r"selling\s*price\b",
    ],
    "PurchasePrice": [
        r"purchase\s*price\b", r"cost\s*price\b", r"buy\s*price\b",
        r"procurement\s*price\b", r"vendor\s*price\b",
    ],
    "Remarks": [
        r"remarks\b", r"notes\b", r"comments\b", r"memo\b",
        r"free\s*text\b", r"additional\s*info\b",
    ],
}

BP_FIELD_PATTERNS = {
    # -----------------------------------------------------------------------
    # Core identity fields
    # -----------------------------------------------------------------------
    "CardCode": [
        r"bpcode\b", r"bp\s*code\b", r"card\s*code\b", r"cardcode\b",
        r"vendor\s*code\b", r"supplier\s*code\b", r"customer\s*code\b",
        r"account\s*no\.?", r"customer\s*id\b", r"cust\s*id\b",
        r"cust(?:omer)?\s*(?:no|num)\b", r"vendor\s*id\b",
        r"party\s*code\b", r"partycode\b",
        r"client\s*id\b", r"client\s*code\b",
        r"parentkey\b", r"recordkey\b",
        # Real-world aliases observed in dynamic data
        r"vend(?:or)?\s*code\b", r"supp(?:lier)?\s*code\b",
        r"creditor\s*code\b", r"debtor\s*code\b",
        r"acc(?:ount)?\s*code\b", r"acc(?:ount)?\s*id\b",
        r"bp\s*id\b", r"partner\s*code\b",
        r"party\s*id\b",
    ],
    "CardName": [
        r"bpname\b", r"bp\s*name\b", r"card\s*name\b", r"cardname\b",
        r"company\s*name\b", r"supplier\s*name\b", r"vendor\s*name\b",
        r"customer\s*name\b", r"business\s*name\b",
        r"\bcompany\b", r"full\s*name\b", r"contact\s*name\b",
        r"organisation\s*name\b",
        # Real-world aliases
        r"party\s*na?m?e?\b",           # "PartyNmae" (typo), "Party Name"
        r"partyname\b", r"partynmae\b",  # explicit typo match
        r"vend(?:or)?\s*name\b", r"supp(?:lier)?\s*name\b",
        r"creditor\s*name\b", r"debtor\s*name\b",
        r"account\s*name\b", r"acc\s*name\b",
        r"firm\s*name\b", r"trade\s*name\b", r"legal\s*name\b",
        r"entity\s*name\b",
    ],
    "FirstName": [
        r"first\s*name\b", r"firstname\b", r"given\s*name\b",
        r"f(?:irst)?\s*name\b",
    ],
    "LastName": [
        r"last\s*name\b", r"lastname\b", r"surname\b",
        r"family\s*name\b", r"l(?:ast)?\s*name\b",
    ],
    "CardType": [
        r"bp\-?\s*type\b", r"bp\s*type\b", r"bptype\b",
        r"card\s*type\b", r"cardtype\b", r"partner\s*type\b",
        r"vendor\s*type\b", r"customer\s*type\b",
        r"business\s*partner\s*type\b",
        # Real-world aliases
        r"party\s*type\b", r"partytype\b",
        r"account\s*type\b", r"acc\s*type\b",
        r"entity\s*type\b", r"supplier\s*type\b",
        r"cust(?:omer)?\s*type\b",
        r"\btype\b",                     # lone "Type" column
    ],

    # -----------------------------------------------------------------------
    # Grouping / classification
    # -----------------------------------------------------------------------
    "GroupCode": [
        r"bp\s*group\b", r"bpgroup\b", r"group\s*code\b", r"groupcode\b",
        r"vendor\s*group\b", r"supplier\s*group\b", r"customer\s*group\b",
        r"party\s*group\b", r"partygroup\b",
        r"account\s*group\b", r"cust(?:omer)?\s*group\b",
        r"category\s*group\b",
    ],

    # -----------------------------------------------------------------------
    # Control / GL accounts
    # -----------------------------------------------------------------------
    "ControlAccount": [
        r"control\s*account\b", r"controlaccount\b",
        r"gl\s*account\b", r"debitor\s*account\b",
        r"creditor\s*account\b", r"reconciliation\s*account\b",
        # Real-world aliases
        r"vendor\s*account\b", r"customer\s*account\b",
        r"party\s*account\b", r"ledger\s*account\b",
        r"account\s*ledger\b", r"gl\s*code\b",
        r"sap\s*gl\s*account\b", r"reconcil(?:iation)?\s*acc\b",
        r"\baccount\b",                  # lone "Account" column in many templates
    ],

    # -----------------------------------------------------------------------
    # Billing address block
    # -----------------------------------------------------------------------
    "BillToBuilding": [
        r"bill(?:ing)?\s*build(?:ing)?\b",
        r"bill(?:ing)?\s*address\s*1\b",
        r"bill(?:ing)?\s*address1\b",
        r"bill(?:ing)?\s*street\s*1\b",
        r"bill(?:ing)?\s*line\s*1\b",
        r"billing\s*premises\b",
    ],
    "Address": [
        r"street\s*address\b", r"billing\s*address\b",
        r"registered\s*address\b", r"mailaddress\b",
        r"address\s*1\b", r"address1\b", r"street\s*1\b",
        r"(?<!email\s)(?<!e-mail\s)\baddress\b",
        # Real-world billing address aliases
        r"bill(?:ing)?\s*add(?:ress)?\b",
        r"bill\s*to\s*address\b", r"b(?:ill(?:ing)?)?\s*addr\b",
        r"ship\s*from\s*address\b",
    ],
    "AddressLine2": [
        r"address\s*2\b", r"address2\b", r"street\s*2\b",
        r"\bapt\.?\b", r"\bsuite\b", r"apartment\b", r"unit\s*no\b",
        r"bill(?:ing)?\s*address\s*2\b", r"bill(?:ing)?\s*address2\b",
        r"bill(?:ing)?\s*line\s*2\b",
    ],
    "BillToCity": [
        r"bill(?:ing)?\s*city\b", r"bill\s*to\s*city\b",
        r"bill(?:ing)?\s*town\b",
    ],
    "City": [
        r"\bcity\b", r"\btown\b", r"district\b",
        r"bill(?:ing)?\s*city\b", r"bill\s*to\s*city\b",
    ],
    "BillToState": [
        r"bill(?:ing)?\s*state\b", r"bill\s*to\s*state\b",
        r"b(?:ill(?:ing)?)?\s*state\b", r"bstate\b",
        r"bill(?:ing)?\s*province\b",
    ],
    "State": [
        r"state\s*/\s*province\b", r"\bstate\b", r"\bprovince\b",
        r"state\s*code\b", r"region\b",
        r"bill(?:ing)?\s*state\b", r"bstate\b",
    ],
    "StateCode": [
        r"state\s*code\b", r"statecode\b", r"province\s*code\b",
        r"bill(?:ing)?\s*state\s*code\b", r"ship(?:ping)?\s*state\s*code\b",
        # "#REF!" placeholder — skip in normalization but recognise column
        r"state\s*ref\b",
    ],
    "BillToZipCode": [
        r"bill(?:ing)?\s*zip(?:\s*code)?\b",
        r"bill\s*to\s*zip(?:\s*code)?\b",
        r"bill[-\s]zip(?:code)?\b",
        r"bill(?:ing)?\s*pin(?:\s*code)?\b",
        r"bill(?:ing)?\s*postal(?:\s*code)?\b",
    ],
    "ZipCode": [
        r"postal\s*code\b", r"zip\s*code\b", r"\bzip\b",
        r"pin\s*code\b", r"\bpincode\b", r"post\s*code\b",
        r"postcode\b",
        r"bill(?:ing)?\s*zip(?:\s*code)?\b",
        r"bill[-\s]zip(?:code)?\b",
    ],
    "BillToCountry": [
        r"bill(?:ing)?\s*country\b", r"bill\s*to\s*country\b",
    ],
    "Country": [
        r"\bcountry\b",
        r"bill(?:ing)?\s*country\b",
    ],

    # -----------------------------------------------------------------------
    # Shipping address block
    # -----------------------------------------------------------------------
    "ShipToBuilding": [
        r"ship(?:ping)?\s*build(?:ing)?\b",
        r"ship\s*to\s*build(?:ing)?\b",
        r"ship(?:ping)?\s*address\s*1\b",
        r"ship(?:ping)?\s*premises\b",
        r"deliver(?:y)?\s*address\s*1\b",
    ],
    "ShipToAddress": [
        r"ship(?:ping)?\s*address\b",
        r"ship\s*to\s*address\b",
        r"deliver(?:y)?\s*address\b",
        r"consignee\s*address\b",
    ],
    "ShipToCity": [
        r"ship(?:ping)?\s*city\b", r"ship\s*to\s*city\b",
        r"deliver(?:y)?\s*city\b", r"consignee\s*city\b",
    ],
    "ShipToState": [
        r"ship(?:ping)?\s*state\b", r"ship\s*to\s*state\b",
        r"deliver(?:y)?\s*state\b",
    ],
    "ShipToZipCode": [
        r"ship(?:ping)?\s*zip(?:\s*code)?\b",
        r"ship\s*to\s*zip(?:\s*code)?\b",
        r"ship(?:ping)?\s*pin(?:\s*code)?\b",
        r"ship(?:ping)?\s*postal(?:\s*code)?\b",
        r"deliver(?:y)?\s*zip(?:\s*code)?\b",
    ],
    "ShipToCountry": [
        r"ship(?:ping)?\s*country\b",
        r"ship\s*to\s*country\b",
        r"deliver(?:y)?\s*country\b",
    ],
    "ShipToStreet": [
        r"ship(?:ping)?\s*street\b",
        r"ship\s*to\s*street\b",
        r"deliver(?:y)?\s*street\b",
        r"consignee\s*street\b",
        # Raw "Street" column seen in sample data
        r"^street$",
    ],

    # -----------------------------------------------------------------------
    # Tax & Compliance
    # -----------------------------------------------------------------------
    "TaxDetails": [
        r"tax\s*details\b", r"taxdetails\b", r"tax\s*code\b",
        r"tax\s*group\b", r"vat\s*group\b",
    ],
    "GSTNo": [
        r"gst\s*no\.?\b", r"gst\s*number\b", r"gstin\b", r"gst\s*id\b",
        r"gst\s*reg\b",
        # Real-world aliases
        r"gstn(?:\s*no\.?)?\b",          # "GSTN No."
        r"bill(?:ing)?\s*gstin\b",       # "Bill GSTIN"
        r"ship(?:ping)?\s*gstin\b",      # "Ship GSTIN"
        r"gst\s*in\b",
        r"gst\s*registration\s*(?:no\.?|number)?\b",
    ],
    "GSTType": [
        r"gst\s*type\b", r"gsttype\b",
        r"tax\s*type\b", r"gst\s*class(?:ification)?\b",
        r"gst\s*regime\b", r"gst\s*scheme\b",
        # Values commonly seen: REGULAR, COMPOSITION, UNREGISTERED
        r"registration\s*type\b",
    ],
    "PANNo": [
        r"pan\s*no\.?\b", r"pan\s*number\b", r"pan\s*card\b",
        r"panno\b", r"pan\b",
        r"p\.?\s*a\.?\s*n\.?\b",         # "P.A.N. No"
        r"income\s*tax\s*pan\b",
    ],
    "FederalTaxID": [
        r"federal\s*tax\s*id\b", r"federaltaxid\b", r"lictradnum\b",
        r"taxid\d*\b", r"tax\s*id\b", r"gstin\b", r"vat\s*no\.?",
        r"pan\b", r"ein\b",
    ],

    # -----------------------------------------------------------------------
    # Contact details
    # -----------------------------------------------------------------------
    "Phone1": [
        r"telephone\b", r"phone\s*1\b", r"phone1\b", r"tel1\b",
        r"primary\s*phone\b", r"contact\s*no\.?", r"\bphone\b",
        r"mobile\s*phone\b", r"mob(?:ile)?\b", r"cell(?:ular)?\b",
        r"contact\s*phone\b", r"direct\s*line\b",
    ],
    "Phone2": [
        r"phone\s*2\b", r"phone2\b", r"tel2\b", r"mobile\b",
        r"alt(?:ernate)?\s*phone\b", r"cell\s*phone\b",
        r"secondary\s*phone\b", r"other\s*phone\b",
    ],
    "EmailAddress": [
        r"email\s*address\b", r"emailaddress\b", r"mailaddres\b",
        r"e-mail\b", r"email\b",
        r"e\s*mail\b", r"electronic\s*mail\b",
        r"contact\s*email\b",
    ],
    "ContactPerson": [
        r"contact\s*person(?:\s*name)?\b",
        r"contactperson\b", r"contact\s*name\b",
        r"key\s*contact\b", r"account\s*manager\b",
        r"representative\b", r"rep\s*name\b",
        r"salesperson\b", r"sales\s*rep\b",
    ],

    # -----------------------------------------------------------------------
    # Financial / payment
    # -----------------------------------------------------------------------
    "Currency": [
        r"currency\b", r"curr(?:ency)?\b",
        r"transaction\s*currency\b", r"base\s*currency\b",
        r"billing\s*currency\b", r"payment\s*currency\b",
    ],
    "PaymentTerms": [
        r"payment\s*terms\b", r"paymentterms\b", r"pay\s*terms\b",
        r"paytermsgrpcod\b", r"credit\s*terms\b",
        r"net\s*days\b", r"due\s*days\b", r"payment\s*days\b",
    ],
    "CreditLimit": [
        r"credit\s*limit\b", r"creditlimit\b",
        r"max(?:imum)?\s*credit\b", r"credit\s*ceiling\b",
        r"approved\s*credit\b",
    ],
    "BankAccount": [
        r"bank\s*account\b", r"bank\s*acc(?:ount)?\b",
        r"bank\s*a\/c\b", r"account\s*number\b",
        r"iban\b", r"bban\b",
    ],
    "BankName": [
        r"bank\s*name\b", r"bankname\b", r"bank\b",
    ],
    "IFSC": [
        r"ifsc\b", r"ifsc\s*code\b", r"bank\s*code\b",
        r"routing\s*number\b", r"sort\s*code\b", r"swift\s*code\b",
        r"bic\b",
    ],

    # -----------------------------------------------------------------------
    # Miscellaneous BP fields
    # -----------------------------------------------------------------------
    "Remarks": [
        r"remarks\b", r"notes\b", r"comments\b", r"memo\b",
        r"free\s*text\b", r"additional\s*info\b", r"description\b",
    ],
    "Website": [
        r"website\b", r"web\s*site\b", r"url\b", r"web\s*address\b",
        r"homepage\b",
    ],
    "Industry": [
        r"industry\b", r"industry\s*type\b", r"sector\b",
        r"business\s*sector\b", r"trade\s*type\b",
    ],
}

WH_FIELD_PATTERNS = {
    "WarehouseCode": [
        r"warehouse\s*code\b", r"whscode\b", r"wh\s*code\b",
        r"storage\s*code\b", r"plant\s*code\b",
        r"parentkey\b", r"recordkey\b",
        r"depot\s*code\b", r"store\s*code\b",
        r"location\s*code\b",
    ],
    "WarehouseName": [
        r"warehouse\s*name\b", r"whsname\b", r"wh\s*name\b",
        r"facility\s*name\b", r"depot\s*name\b",
        r"store\s*name\b", r"storage\s*name\b",
    ],
    "Location": [
        r"location\s*code\b", r"location\s*id\b", r"location\b",
        r"olct\b", r"bin\s*location\b",
    ],
    "Address": [
        r"warehouse\s*address\b", r"whs\s*address\b",
        r"facility\s*address\b", r"street\s*address\b",
        r"location\s*address\b", r"address\b",
    ],
    "Inactive": [r"inactive\b", r"status\b"],
    "BinActivat": [
        r"bin\s*activation\b", r"binactivat\b",
        r"enable\s*bins\b", r"bin\s*locations\b",
    ],
    "Street": [r"street\b", r"road\b"],
    "City": [r"city\b", r"town\b"],
    "Country": [r"country\b"],
    "State": [r"state\b", r"province\b"],
    "ZipCode": [
        r"postal\s*code\b", r"zip\s*code\b", r"\bzip\b",
        r"pin\s*code\b", r"postcode\b",
    ],
}

# ---------------------------------------------------------------------------
# Merged reference: every known SAP target field across all master types.
# Used by get_ai_column_mapping() to validate AI responses.
# ---------------------------------------------------------------------------
_ALL_SAP_FIELDS: Dict[str, List[str]] = {
    **ITEM_FIELD_PATTERNS,
    **BP_FIELD_PATTERNS,
    **WH_FIELD_PATTERNS,
}

# ---------------------------------------------------------------------------
# Extended raw-header normalisation table.
#
# Maps exact (case-insensitive, whitespace-normalised) column labels that appear
# in real-world vendor/customer master sheets to their canonical SAP field
# name.  This table is consulted FIRST by _fuzzy_match_header() before the
# heavier regex scan is attempted, giving O(1) lookup for known aliases.
# ---------------------------------------------------------------------------
_STATIC_HEADER_ALIASES: Dict[str, str] = {
    # ---- Core identity ----
    "vendor code":          "CardCode",
    "vendorcode":           "CardCode",
    "vendor no":            "CardCode",
    "vendor no.":           "CardCode",
    "vend code":            "CardCode",
    "supplier code":        "CardCode",
    "suppliercode":         "CardCode",
    "customer code":        "CardCode",
    "customercode":         "CardCode",
    "cust code":            "CardCode",
    "cust id":              "CardCode",
    "customer id":          "CardCode",
    "party code":           "CardCode",
    "partycode":            "CardCode",
    "bp code":              "CardCode",
    "bpcode":               "CardCode",
    "card code":            "CardCode",
    "cardcode":             "CardCode",
    "account no":           "CardCode",
    "account no.":          "CardCode",
    "acc no":               "CardCode",
    "client code":          "CardCode",
    "client id":            "CardCode",

    "vendor name":          "CardName",
    "vendorname":           "CardName",
    "vendor nm":            "CardName",
    "supplier name":        "CardName",
    "suppliername":         "CardName",
    "customer name":        "CardName",
    "customername":         "CardName",
    "cust name":            "CardName",
    "company name":         "CardName",
    "party name":           "CardName",
    "partynmae":            "CardName",   # common typo
    "partyname":            "CardName",
    "mg creative":          "CardName",   # unlikely column header but safe to map
    "bp name":              "CardName",
    "bpname":               "CardName",
    "card name":            "CardName",
    "cardname":             "CardName",
    "account name":         "CardName",
    "firm name":            "CardName",
    "trade name":           "CardName",
    "legal name":           "CardName",

    # ---- Type / group ----
    "vendor type":          "CardType",
    "supplier type":        "CardType",
    "customer type":        "CardType",
    "party type":           "CardType",
    "type":                 "CardType",
    "bp type":              "CardType",
    "bptype":               "CardType",
    "card type":            "CardType",
    "cardtype":             "CardType",

    "vendor group":         "GroupCode",
    "supplier group":       "GroupCode",
    "customer group":       "GroupCode",
    "party group":          "GroupCode",
    "partygroup":           "GroupCode",
    "bp group":             "GroupCode",
    "account group":        "GroupCode",

    # ---- Control account ----
    "vendor account":       "ControlAccount",
    "customer account":     "ControlAccount",
    "party account":        "ControlAccount",
    "ledger account":       "ControlAccount",
    "gl account":           "ControlAccount",
    "gl code":              "ControlAccount",
    "account":              "ControlAccount",
    "control account":      "ControlAccount",

    # ---- Currency ----
    "curr":                 "Currency",
    "currency":             "Currency",
    "curr.":                "Currency",
    "transaction currency": "Currency",

    # ---- Billing address block ----
    "bill building":        "BillToBuilding",
    "bill to building":     "BillToBuilding",
    "billing building":     "BillToBuilding",
    "bill address 1":       "BillToBuilding",
    "billing address 1":    "BillToBuilding",
    "billing address":      "Address",
    "bill to address":      "Address",
    "bill addr":            "Address",
    "billing addr":         "Address",

    "bill to city":         "BillToCity",
    "billing city":         "BillToCity",
    "bill city":            "BillToCity",

    "bill to state":        "BillToState",
    "billing state":        "BillToState",
    "bill state":           "BillToState",
    "bstate":               "BillToState",

    "bill-zipcode":         "BillToZipCode",
    "bill zipcode":         "BillToZipCode",
    "bill to zipcode":      "BillToZipCode",
    "bill to zip code":     "BillToZipCode",
    "billing zip":          "BillToZipCode",
    "billing zip code":     "BillToZipCode",
    "billing pincode":      "BillToZipCode",
    "bill to pin code":     "BillToZipCode",

    "bill to country":      "BillToCountry",
    "billing country":      "BillToCountry",
    "bill country":         "BillToCountry",

    "bill gstin":           "GSTNo",
    "billing gstin":        "GSTNo",
    "bill to gstin":        "GSTNo",

    "state code":           "StateCode",
    "statecode":            "StateCode",

    # ---- Shipping address block ----
    "ship to building":     "ShipToBuilding",
    "shipping building":    "ShipToBuilding",
    "ship building":        "ShipToBuilding",
    "ship address 1":       "ShipToBuilding",

    "street":               "ShipToStreet",    # raw "Street" col seen in sample
    "ship to street":       "ShipToStreet",
    "shipping street":      "ShipToStreet",
    "ship street":          "ShipToStreet",

    "ship to city":         "ShipToCity",
    "shipping city":        "ShipToCity",
    "ship city":            "ShipToCity",
    "delivery city":        "ShipToCity",

    "ship to state":        "ShipToState",
    "shipping state":       "ShipToState",
    "ship state":           "ShipToState",

    "ship to zip code":     "ShipToZipCode",
    "shipping zip":         "ShipToZipCode",
    "ship zip":             "ShipToZipCode",
    "ship to pin code":     "ShipToZipCode",

    "ship to country":      "ShipToCountry",
    "shipping country":     "ShipToCountry",
    "ship country":         "ShipToCountry",

    "ship gstin":           "GSTNo",
    "shipping gstin":       "GSTNo",
    "ship to gstin":        "GSTNo",
    "gstn no.":             "GSTNo",
    "gstn no":              "GSTNo",
    "gstn":                 "GSTNo",
    "gstin":                "GSTNo",
    "gst no":               "GSTNo",
    "gst no.":              "GSTNo",
    "gst number":           "GSTNo",

    # ---- GST type ----
    "gst type":             "GSTType",
    "gsttype":              "GSTType",
    "registration type":    "GSTType",
    "tax type":             "GSTType",

    # ---- PAN ----
    "p.a.n. no":            "PANNo",
    "p.a.n. no.":           "PANNo",
    "pan no":               "PANNo",
    "pan no.":              "PANNo",
    "pan number":           "PANNo",
    "pan card":             "PANNo",
    "pan":                  "PANNo",

    # ---- Contact ----
    "mobile phone":         "Phone1",
    "mobile":               "Phone1",
    "phone":                "Phone1",
    "telephone":            "Phone1",
    "contact no":           "Phone1",
    "contact no.":          "Phone1",
    "contact number":       "Phone1",

    "e-mail":               "EmailAddress",
    "email":                "EmailAddress",
    "email address":        "EmailAddress",
    "e mail":               "EmailAddress",

    "contact person name":  "ContactPerson",
    "contact person":       "ContactPerson",
    "contact name":         "ContactPerson",
    "key contact":          "ContactPerson",

    # ---- Payments ----
    "payment terms":        "PaymentTerms",
    "pay terms":            "PaymentTerms",
    "credit terms":         "PaymentTerms",

    "credit limit":         "CreditLimit",

    # ---- Banking ----
    "bank account":         "BankAccount",
    "bank a/c":             "BankAccount",
    "ifsc":                 "IFSC",
    "ifsc code":            "IFSC",
    "bank name":            "BankName",

    # ---- Item master extras ----
    "item code":            "ItemCode",
    "itemcode":             "ItemCode",
    "item no":              "ItemCode",
    "item no.":             "ItemCode",
    "part no":              "ItemCode",
    "part no.":             "ItemCode",
    "part number":          "ItemCode",
    "sku":                  "ItemCode",
    "product code":         "ItemCode",
    "material no":          "ItemCode",
    "material code":        "ItemCode",

    "item name":            "ItemName",
    "itemname":             "ItemName",
    "description":          "ItemName",
    "item description":     "ItemName",
    "product name":         "ItemName",
    "material description": "ItemName",

    "item group":           "ItemsGroupCode",
    "item group code":      "ItemsGroupCode",
    "category code":        "ItemsGroupCode",

    "uom":                  "InventoryUOM",
    "unit":                 "InventoryUOM",
    "unit of measure":      "InventoryUOM",
    "base uom":             "InventoryUOM",

    "hsn":                  "HSN",
    "hsn code":             "HSN",
    "sac":                  "HSN",
    "sac code":             "HSN",
    "hs code":              "HSN",

    "tax rate":             "TaxRate",
    "gst rate":             "TaxRate",
    "vat rate":             "TaxRate",
    "tax %":                "TaxRate",

    "barcode":              "BarCode",
    "bar code":             "BarCode",
    "ean":                  "BarCode",

    # ---- Warehouse master extras ----
    "warehouse code":       "WarehouseCode",
    "whscode":              "WarehouseCode",
    "wh code":              "WarehouseCode",
    "warehouse name":       "WarehouseName",
    "whsname":              "WarehouseName",
    "wh name":              "WarehouseName",
    "bin activation":       "BinActivat",
    "bin locations":        "BinActivat",
    "inactive":             "Inactive",
}


# ---------------------------------------------------------------------------
# Helper: normalise a raw header string for alias lookup
# ---------------------------------------------------------------------------

def _normalise_header_key(raw: str) -> str:
    """
    Lower-case, collapse internal whitespace, strip leading/trailing noise
    so that 'Bill-ZipCode', '  Bill ZipCode ', and 'bill zipcode' all map
    to the same lookup key 'bill zipcode'.
    """
    s = raw.strip().lower()
    # Replace hyphens/underscores with spaces
    s = re.sub(r"[-_]+", " ", s)
    # Collapse multiple spaces
    s = re.sub(r"\s{2,}", " ", s)
    return s


def _fuzzy_match_header(raw_header: str, patterns: Dict[str, List[str]]) -> Optional[str]:
    """
    Two-stage header → SAP field resolution:

    Stage 1 — O(1) static alias lookup.
        Normalise the raw header text and check _STATIC_HEADER_ALIASES.

    Stage 2 — Regex scan (original behaviour, unchanged).
        Walk the supplied patterns dict and return the first matching field name.

    Returns the SAP field name string, or None if no match is found.
    """
    key = _normalise_header_key(raw_header)

    # Stage 1: static alias table
    if key in _STATIC_HEADER_ALIASES:
        return _STATIC_HEADER_ALIASES[key]

    # Stage 2: regex patterns
    for field, pats in patterns.items():
        for p in pats:
            if (
                re.search(rf"^(?:.*?\b)?(?:{p})[:\s]*$", raw_header, re.IGNORECASE)
                or re.search(rf"\b{p}\b", raw_header, re.IGNORECASE)
            ):
                return field

    return None


def detect_master_type_from_text(text: str) -> MasterDataType:
    """Analyze keyword frequencies to identify the master data category."""
    text_lower = text.lower()
    item_score = sum(
        1 for kw in [
            "item code", "item no", "itemcode", "inventory",
            "sales item", "purchase item", "barcode", "uom", "itmsgrpcod",
            "hsn", "sac", "sku", "part number",
        ] if kw in text_lower
    )
    bp_score = sum(
        1 for kw in [
            "cardcode", "card code", "card name", "lictradnum", "federaltaxid",
            "vendor", "supplier", "customer", "card type", "gstin", "tax id",
            "partycode", "party code", "party name", "partynmae",
            "vendor code", "vendor name", "gstn", "bill to city",
            "ship to building", "contact person",
        ] if kw in text_lower
    )
    wh_score = sum(
        1 for kw in [
            "warehouse code", "warehouse name", "whscode", "whsname",
            "bin location", "storage facility", "depot",
        ] if kw in text_lower
    )

    scores = {
        MasterDataType.ITEM: item_score,
        MasterDataType.BUSINESS_PARTNER: bp_score,
        MasterDataType.WAREHOUSE: wh_score,
    }
    best_type = max(scores, key=scores.get)
    return best_type if scores[best_type] > 0 else MasterDataType.ITEM


def extract_key_values_with_patterns(
    text: str,
    patterns_dict: Dict[str, List[str]]
) -> Dict[str, Any]:
    """Parse text lines using regex key-value patterns (e.g. 'Field: Value')."""
    extracted: Dict[str, Any] = {}
    lines = text.split("\n")

    for field, patterns in patterns_dict.items():
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue
            for pat in patterns:
                m = re.search(
                    rf"^(?:.*?\b)?(?:{pat})\s*[:\-\|\=]\s*(.+)$",
                    line_clean,
                    re.IGNORECASE
                )
                if m:
                    extracted[field] = m.group(1).strip()
                    break
            if field in extracted:
                break
    return extracted


def load_spreadsheet_rows(
    file_path: str,
    master_type: Optional[MasterDataType] = None
) -> List[List[str]]:
    """
    Reads rows from an Excel (.xlsx, .xls) or CSV file as a list of string cells.
    If master_type is specified and the workbook has multiple sheets, selects the
    sheet that best matches master_type.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    rows: List[List[str]] = []

    if ext == ".csv":
        encoding = "utf-8"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                sample = f.read(2048)
        except UnicodeDecodeError:
            encoding = "latin-1"
            with open(file_path, "r", encoding="latin-1") as f:
                sample = f.read(2048)

        with open(file_path, "r", encoding=encoding, errors="ignore") as f:
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except Exception:
                dialect = "excel"
            f.seek(0)
            reader = csv.reader(f, dialect=dialect)
            for r in reader:
                cleaned_row = [str(c).strip() for c in r]
                if any(cleaned_row):
                    rows.append(cleaned_row)
        return rows

    elif ext in [".xlsx", ".xlsm", ".xltx"]:
        wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        sheets = wb.worksheets
        target_sheets = sheets

        if len(sheets) > 1 and master_type:
            mt_str = (
                master_type.value
                if hasattr(master_type, "value")
                else str(master_type).lower()
            )
            matching = []
            for s in sheets:
                s_name = s.title.lower()
                if mt_str in [
                    "business_partner", "businesspartner", "bp",
                    "vendor", "supplier", "customer",
                ]:
                    if any(
                        w in s_name
                        for w in ["vendor", "supplier", "customer",
                                  "business", "partner", "bp"]
                    ):
                        matching.append(s)
                elif mt_str in ["item", "items"]:
                    if any(
                        w in s_name
                        for w in ["item", "product", "material", "part", "oitm"]
                    ):
                        matching.append(s)
                elif mt_str in ["warehouse", "warehouses"]:
                    if any(
                        w in s_name
                        for w in ["warehouse", "whs", "store", "depot", "owhs"]
                    ):
                        matching.append(s)
            target_sheets = matching[:1] if matching else sheets[:1]
        elif len(sheets) > 1:
            target_sheets = sheets[:1]

        for sheet in target_sheets:
            for r in sheet.iter_rows(values_only=True):
                if any(c is not None for c in r):
                    cleaned_row = [
                        str(c).strip() if c is not None else "" for c in r
                    ]
                    if any(cleaned_row):
                        rows.append(cleaned_row)
        wb.close()
        return rows

    else:
        try:
            import pandas as pd
            df = pd.read_excel(file_path, header=None)
            for _, r in df.iterrows():
                cleaned_row = [
                    str(c).strip() if pd.notna(c) else "" for c in r
                ]
                if any(cleaned_row):
                    rows.append(cleaned_row)
            return rows
        except Exception:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    parts = [p.strip() for p in line.split(",")]
                    if any(parts):
                        rows.append(parts)
            return rows


COMMON_TABLE_HEADERS = {
    "#", "no", "no.", "sl no", "sl no.", "sr no", "sr. no.", "line", "linenum",
    "parentkey", "recordkey", "foreign name", "comments", "remarks",
    "specification value", "field name",
}


def is_field_label(text: str, patterns: Dict[str, List[str]]) -> bool:
    """Returns True if text matches any field pattern or table header keyword."""
    clean = text.strip()
    if not clean:
        return False
    if clean.lower() in COMMON_TABLE_HEADERS:
        return True
    # Check static alias table first (fast path)
    if _normalise_header_key(clean) in _STATIC_HEADER_ALIASES:
        return True
    for pats in patterns.values():
        for p in pats:
            if (
                re.search(rf"^(?:.*?\b)?(?:{p})[:\s]*$", clean, re.IGNORECASE)
                or re.search(rf"^{p}$", clean, re.IGNORECASE)
            ):
                return True
    return False


def parse_spreadsheet_data(
    rows: List[List[str]],
    patterns: Dict[str, List[str]],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Parses spreadsheet rows into structured records.

    Enhancements over original:
    - Uses _fuzzy_match_header() (static alias + regex) instead of raw regex
      so aliased columns like 'Partycode', 'PartyNmae', 'BState', 'Curr',
      'Bill Building', 'Ship to Building', 'GSTN No.' etc. are resolved
      without requiring the AI to be available.
    - Everything else (multi-level headers, key-value fallback, normalization)
      is preserved verbatim.
    """
    header_col_map: Dict[int, str] = {}
    data_start_idx = -1

    # 1. Scan for tabular header row(s)
    for r_idx, row in enumerate(rows):
        non_empty = [c for c in row if c.strip()]
        if not non_empty:
            continue

        matched: Dict[int, str] = {}
        for c_idx, cell in enumerate(row):
            cell_clean = cell.strip()
            if not cell_clean:
                continue
            if c_idx not in matched:
                sap_field = _fuzzy_match_header(cell_clean, patterns)
                if sap_field and sap_field not in matched.values():
                    matched[c_idx] = sap_field

        is_header = False
        if len(matched) >= 2:
            is_header = True
        elif len(matched) >= 1 and len(non_empty) <= len(matched) + 2:
            if all(
                c_idx in matched or is_field_label(cell, patterns)
                for c_idx, cell in enumerate(row)
                if cell.strip()
            ):
                is_header = True

        if is_header:
            header_col_map.update(matched)
            continue
        elif header_col_map:
            data_start_idx = r_idx
            break

    records: List[Dict[str, Any]] = []
    if header_col_map and data_start_idx >= 0:
        for r_idx in range(data_start_idx, len(rows)):
            row = rows[r_idx]
            rec: Dict[str, Any] = {}
            for c_idx, field in header_col_map.items():
                if c_idx < len(row) and row[c_idx].strip():
                    val = row[c_idx].strip()
                    # Skip Excel formula errors in data cells
                    if val.upper() in ("#REF!", "#N/A", "#VALUE!", "#DIV/0!"):
                        continue
                    rec[field] = val
            if rec:
                records.append(normalization_service.normalize_dict(rec))

    # Fallback to key-value format if tabular parsing yielded no records
    if not records:
        kv_data: Dict[str, Any] = {}
        for r in rows:
            if len(r) >= 2 and r[0].strip() and r[1].strip():
                k_cand = r[0].strip()
                v_cand = r[1].strip()
                sap_field = _fuzzy_match_header(k_cand, patterns)
                if sap_field and sap_field not in kv_data:
                    if not is_field_label(v_cand, patterns):
                        if v_cand.upper() not in (
                            "#REF!", "#N/A", "#VALUE!", "#DIV/0!"
                        ):
                            kv_data[sap_field] = v_cand
        if kv_data:
            records = [normalization_service.normalize_dict(kv_data)]

    primary = records[0] if records else {}
    return primary, records


# ---------------------------------------------------------------------------
# AI-Driven Column Mapping Helpers
# ---------------------------------------------------------------------------

def _find_header_row(rows: List[List[str]]) -> Tuple[int, List[str]]:
    """
    Find the index and contents of the most likely header row.
    Looks for the first row that has ≥2 non-empty, non-numeric cells.
    Returns (-1, []) if no suitable header row is found.
    """
    for idx, row in enumerate(rows):
        non_empty = [c.strip() for c in row if c.strip()]
        if len(non_empty) < 2:
            continue
        non_numeric = [
            c for c in non_empty
            if not c.replace(".", "").replace("-", "").isdigit()
        ]
        if len(non_numeric) >= 2:
            return idx, [c.strip() for c in row]
    return -1, []


_AI_MAPPING_CACHE: Dict[Tuple[Tuple[str, ...], str], Optional[Dict[str, str]]] = {}

async def get_ai_column_mapping(
    headers: List[str],
    master_type: Optional[MasterDataType] = None,
    timeout: float = 4.0,
) -> Optional[Dict[str, str]]:
    """
    Send raw Excel column headers to NVIDIA Nemotron and obtain a strict JSON
    mapping of {ExcelHeader: SAPFieldName}.

    Returns a dict on success, or None on failure/timeout (callers fall back
    to _fuzzy_match_header / regex).
    """
    from app.services.chat_service import nvidia_chat_service

    if not headers:
        return None

    # 1. Fast path: If static alias & regex mapping already resolves key identifier
    # (CardCode, ItemCode, WarehouseCode) and >= 2 columns, or all headers, return instantly!
    static_mapped = {h: _fuzzy_match_header(h, _ALL_SAP_FIELDS) for h in headers}
    resolved = {h: v for h, v in static_mapped.items() if v is not None}
    has_key_id = any(v in ("CardCode", "ItemCode", "WarehouseCode") for v in resolved.values())
    if (has_key_id and len(resolved) >= 2) or (len(resolved) == len(headers) and len(resolved) > 0):
        logger.info(
            f"Static alias table resolved {len(resolved)}/{len(headers)} columns "
            f"(including key identifier). Skipping AI network call."
        )
        return resolved

    # 2. In-memory cache check across concurrent extraction engines
    cache_key = (tuple(headers), str(master_type))
    if cache_key in _AI_MAPPING_CACHE:
        return _AI_MAPPING_CACHE[cache_key]

    known_fields = sorted(_ALL_SAP_FIELDS.keys())
    type_hint = (
        f"Master data type: {master_type.value}"
        if master_type and master_type != MasterDataType.UNKNOWN
        else "Master data type: unknown (auto-detect)"
    )

    system_prompt = (
        "You are an SAP data integration expert.\n"
        "Your ONLY task is to map Excel column headers to their canonical SAP field names.\n"
        "Respond with ONLY a valid JSON object — no markdown fences, no explanation, no extra text.\n"
        'Format: {"ExcelHeader": "SAPFieldName", ...}\n'
        "Rules:\n"
        "  • Only include headers that clearly match a known SAP field.\n"
        "  • Omit headers that do not match any SAP field.\n"
        "  • Use only field names from the 'Known SAP target fields' list.\n"
        "  • Never invent field names not on that list.\n"
        "  • Handle common aliases: e.g. 'Curr'→Currency, 'PartyNmae'→CardName,\n"
        "    'BState'→BillToState, 'Partycode'→CardCode, 'Vendor Group'→GroupCode,\n"
        "    'Vendor Account'→ControlAccount, 'Bill Building'→BillToBuilding,\n"
        "    'Ship to Building'→ShipToBuilding, 'GSTN No.'→GSTNo,\n"
        "    'P.A.N. No'→PANNo, 'GST Type'→GSTType,\n"
        "    'Contact Person Name'→ContactPerson."
    )

    known_str = ", ".join(known_fields)
    user_prompt = (
        f"{type_hint}\n\n"
        f"Excel headers to map: {headers}\n\n"
        f"Known SAP target fields: {known_str}\n\n"
        "Return ONLY the JSON mapping object."
    )

    try:
        raw = await asyncio.wait_for(
            nvidia_chat_service.generate(
                system_prompt=system_prompt, user_prompt=user_prompt
            ),
            timeout=timeout,
        )

        cleaned = re.sub(r"^```(?:json)?", "", raw.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            logger.warning("AI column mapping: no JSON object found in LLM response.")
            _AI_MAPPING_CACHE[cache_key] = None
            return None

        mapping: Dict[str, str] = json.loads(cleaned[start : end + 1])

        valid: Dict[str, str] = {
            k: v
            for k, v in mapping.items()
            if isinstance(k, str) and isinstance(v, str) and v in _ALL_SAP_FIELDS
        }

        if not valid:
            logger.warning(
                "AI column mapping returned no valid SAP field entries — "
                "using fuzzy/regex fallback."
            )
            _AI_MAPPING_CACHE[cache_key] = None
            return None

        logger.info(
            f"AI column mapping succeeded with {len(valid)} fields: "
            f"{list(valid.values())}"
        )
        _AI_MAPPING_CACHE[cache_key] = valid
        return valid

    except asyncio.TimeoutError:
        logger.warning(
            f"AI column mapping timed out after {timeout}s — "
            "using fuzzy/regex fallback."
        )
        _AI_MAPPING_CACHE[cache_key] = None
        return None
    except json.JSONDecodeError as jde:
        logger.warning(
            f"AI column mapping returned non-JSON response ({jde}) — "
            "using fuzzy/regex fallback."
        )
        _AI_MAPPING_CACHE[cache_key] = None
        return None
    except Exception as exc:
        logger.warning(
            f"AI column mapping failed ({exc}) — using fuzzy/regex fallback."
        )
        _AI_MAPPING_CACHE[cache_key] = None
        return None


def parse_spreadsheet_data_with_mapping(
    data_rows: List[List[str]],
    col_index_map: Dict[int, str],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Deterministic parser that consumes a pre-computed {column_index: SAP_field}
    map and maps each data row into a structured record.

    Skips Excel formula error strings (#REF!, #N/A, etc.) in data cells.
    """
    if not col_index_map:
        return {}, []

    # Formula error sentinel values to skip
    _EXCEL_ERRORS = {"#REF!", "#N/A", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!"}

    records: List[Dict[str, Any]] = []

    for row in data_rows:
        rec: Dict[str, Any] = {}
        for col_idx, sap_field in col_index_map.items():
            if col_idx < len(row):
                cell_val = row[col_idx].strip()
                if cell_val and cell_val.upper() not in _EXCEL_ERRORS:
                    rec[sap_field] = cell_val

        if rec:
            records.append(normalization_service.normalize_dict(rec))

    primary = records[0] if records else {}
    return primary, records


def _build_col_index_map(
    header_cells: List[str],
    ai_mapping: Dict[str, str],
) -> Dict[int, str]:
    """
    Given the raw header row cells and the AI {ExcelHeader -> SAPField} mapping,
    return a {column_index -> SAPField} dict.

    Matching is case-insensitive and whitespace-normalised.  If a cell is not
    found in the AI mapping, _fuzzy_match_header() is tried as a supplement so
    that columns the AI missed but the static alias table knows are still mapped.
    """
    col_index_map: Dict[int, str] = {}
    normalised_ai: Dict[str, str] = {
        k.strip().lower(): v for k, v in ai_mapping.items()
    }
    already_mapped_fields: set = set()

    for i, cell in enumerate(header_cells):
        key = cell.strip().lower()
        if not key:
            continue

        sap_field: Optional[str] = None

        # AI mapping first
        if key in normalised_ai:
            sap_field = normalised_ai[key]

        # Supplement with static alias / regex if AI didn't cover this column
        if sap_field is None:
            sap_field = _fuzzy_match_header(cell, _ALL_SAP_FIELDS)

        if sap_field and sap_field not in already_mapped_fields:
            col_index_map[i] = sap_field
            already_mapped_fields.add(sap_field)

    return col_index_map


# ---------------------------------------------------------------------------
# Multi-method extractor
# ---------------------------------------------------------------------------

class MultiMethodExtractor:
    # ------------------------------------------------------------------
    # PDF Extraction Methods (unchanged)
    # ------------------------------------------------------------------
    @staticmethod
    def extract_method_1_pymupdf(
        pdf_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> SingleExtractorOutput:
        """Method 1: PyMuPDF (fitz) text block extraction."""
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                blocks = page.get_text("blocks")
                blocks.sort(key=lambda b: (b[1], b[0]))
                for b in blocks:
                    full_text += b[4] + "\n"
            doc.close()

            detected_type = master_type or detect_master_type_from_text(full_text)
            patterns = (
                ITEM_FIELD_PATTERNS
                if detected_type == MasterDataType.ITEM
                else BP_FIELD_PATTERNS
                if detected_type == MasterDataType.BUSINESS_PARTNER
                else WH_FIELD_PATTERNS
            )
            raw_data = extract_key_values_with_patterns(full_text, patterns)
            normalized = normalization_service.normalize_dict(raw_data)

            return SingleExtractorOutput(
                method="pymupdf",
                success=True,
                master_type=detected_type,
                data=normalized,
                raw_text=full_text[:2000],
            )
        except Exception as e:
            logger.error(f"Method 1 (PyMuPDF) failed: {e}")
            return SingleExtractorOutput(
                method="pymupdf", success=False, error_message=str(e)
            )

    @staticmethod
    def extract_method_2_pdfplumber(
        pdf_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> SingleExtractorOutput:
        """Method 2: pdfplumber table and text extraction."""
        try:
            full_text = ""
            table_data: Dict[str, Any] = {}
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    full_text += (page.extract_text() or "") + "\n"
                    tables = page.extract_tables()
                    for tbl in tables:
                        for row in tbl:
                            if not row or len(row) < 2:
                                continue
                            k = str(row[0] or "").strip()
                            v = str(row[1] or "").strip()
                            if k and v:
                                table_data[k] = v

            detected_type = master_type or detect_master_type_from_text(full_text)
            patterns = (
                ITEM_FIELD_PATTERNS
                if detected_type == MasterDataType.ITEM
                else BP_FIELD_PATTERNS
                if detected_type == MasterDataType.BUSINESS_PARTNER
                else WH_FIELD_PATTERNS
            )

            raw_data = extract_key_values_with_patterns(full_text, patterns)
            for tbl_k, tbl_v in table_data.items():
                sap_field = _fuzzy_match_header(tbl_k, patterns)
                if sap_field and sap_field not in raw_data:
                    raw_data[sap_field] = tbl_v

            normalized = normalization_service.normalize_dict(raw_data)

            return SingleExtractorOutput(
                method="pdfplumber",
                success=True,
                master_type=detected_type,
                data=normalized,
                raw_text=full_text[:2000],
            )
        except Exception as e:
            logger.error(f"Method 2 (pdfplumber) failed: {e}")
            return SingleExtractorOutput(
                method="pdfplumber", success=False, error_message=str(e)
            )

    @staticmethod
    def extract_method_3_ocr_or_layout(
        pdf_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> SingleExtractorOutput:
        """Method 3: OCR fallback using pytesseract or rendered page layout."""
        try:
            full_text = ""
            doc = fitz.open(pdf_path)

            if PYTESSERACT_AVAILABLE:
                try:
                    for page in doc:
                        pix = page.get_pixmap(dpi=150)
                        img = Image.open(io.BytesIO(pix.tobytes("png")))
                        ocr_txt = pytesseract.image_to_string(img)
                        full_text += ocr_txt + "\n"
                except Exception as ocr_err:
                    logger.warning(
                        f"Pytesseract skipped/failed: {ocr_err}, "
                        "falling back to fitz text stream"
                    )
                    full_text = ""
                    for page in doc:
                        full_text += (
                            page.get_text(
                                "text",
                                flags=fitz.TEXT_PRESERVE_LIGATURES,
                            )
                            + "\n"
                        )
            else:
                for page in doc:
                    full_text += page.get_text("text") + "\n"

            doc.close()

            detected_type = master_type or detect_master_type_from_text(full_text)
            patterns = (
                ITEM_FIELD_PATTERNS
                if detected_type == MasterDataType.ITEM
                else BP_FIELD_PATTERNS
                if detected_type == MasterDataType.BUSINESS_PARTNER
                else WH_FIELD_PATTERNS
            )
            raw_data = extract_key_values_with_patterns(full_text, patterns)
            normalized = normalization_service.normalize_dict(raw_data)

            return SingleExtractorOutput(
                method="ocr_layout",
                success=True,
                master_type=detected_type,
                data=normalized,
                raw_text=full_text[:2000],
            )
        except Exception as e:
            logger.error(f"Method 3 (OCR/Layout) failed: {e}")
            return SingleExtractorOutput(
                method="ocr_layout", success=False, error_message=str(e)
            )

    # ------------------------------------------------------------------
    # Excel & CSV Extraction Methods  (async with AI + fuzzy fallback)
    # ------------------------------------------------------------------

    @classmethod
    async def extract_excel_method_1_grid(
        cls,
        file_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> SingleExtractorOutput:
        """
        Method 1: Excel Grid & Key-Value cell scanner.

        Resolution priority for each column header:
          1. AI (Nemotron) mapping
          2. Static alias table (_STATIC_HEADER_ALIASES)
          3. Regex pattern scan
        """
        try:
            rows = load_spreadsheet_rows(file_path, master_type=master_type)
            all_text = "\n".join(" ".join(c for c in r if c) for r in rows)
            detected_type = master_type or detect_master_type_from_text(all_text)
            patterns = (
                ITEM_FIELD_PATTERNS
                if detected_type == MasterDataType.ITEM
                else BP_FIELD_PATTERNS
                if detected_type == MasterDataType.BUSINESS_PARTNER
                else WH_FIELD_PATTERNS
            )

            header_idx, header_cells = _find_header_row(rows)
            raw_headers = [c for c in header_cells if c]

            ai_mapping: Optional[Dict[str, str]] = None
            primary_data: Dict[str, Any] = {}
            records: List[Dict[str, Any]] = []

            if raw_headers:
                ai_mapping = await get_ai_column_mapping(
                    raw_headers, master_type=detected_type
                )

            if header_idx >= 0:
                # _build_col_index_map uses AI result then supplements with
                # static alias / regex for any columns the AI missed
                col_index_map = _build_col_index_map(
                    header_cells, ai_mapping or {}
                )
                if col_index_map:
                    data_rows = rows[header_idx + 1:]
                    primary_data, records = parse_spreadsheet_data_with_mapping(
                        data_rows, col_index_map
                    )
                    src = "AI+fuzzy" if ai_mapping else "fuzzy/regex"
                    logger.info(
                        f"[Method 1 Grid] {src} mapping used — "
                        f"{len(records)} records parsed."
                    )

            if not records:
                logger.info(
                    "[Method 1 Grid] Falling back to regex parse_spreadsheet_data()."
                )
                primary_data, records = parse_spreadsheet_data(rows, patterns)

            raw_data: Dict[str, Any] = dict(primary_data)

            # Key-value cell scanner fallback (only when no tabular records were parsed)
            if not records:
                for r in rows:
                    label_count = sum(
                        1 for c in r if is_field_label(c, patterns)
                    )
                    if label_count >= 2:
                        continue

                    for i, cell_text in enumerate(r):
                        cell_text = cell_text.strip()
                        if not cell_text:
                            continue
                        if cell_text.upper() in (
                            "#REF!", "#N/A", "#VALUE!", "#DIV/0!"
                        ):
                            continue

                        # Inline "Key: Value"
                        for field, pats in patterns.items():
                            if field not in raw_data:
                                for p in pats:
                                    m = re.search(
                                        rf"^(?:.*?\b)?(?:{p})\s*[:\-\=]\s*(.+)$",
                                        cell_text,
                                        re.IGNORECASE,
                                    )
                                    if m:
                                        candidate = m.group(1).strip()
                                        if "|" in candidate:
                                            continue
                                        if field == "EmailAddress" and (
                                            "@" not in candidate or "|" in candidate
                                        ):
                                            continue
                                        if not is_field_label(candidate, patterns):
                                            raw_data[field] = candidate
                                            break

                        # Label in cell → value in next non-empty cell
                        sap_field = _fuzzy_match_header(cell_text, patterns)
                        if sap_field and sap_field not in raw_data:
                            for j in range(i + 1, len(r)):
                                val = r[j].strip()
                                if val:
                                    if "|" in val:
                                        continue
                                    if val.upper() in (
                                        "#REF!", "#N/A", "#VALUE!", "#DIV/0!"
                                    ):
                                        continue
                                    if sap_field == "EmailAddress" and (
                                        "@" not in val or "|" in val
                                    ):
                                        continue
                                    if not is_field_label(val, patterns):
                                        raw_data[sap_field] = val
                                    break

            normalized = normalization_service.normalize_dict(raw_data)
            return SingleExtractorOutput(
                method="excel_grid",
                success=True,
                master_type=detected_type,
                data=normalized,
                records=records,
                raw_text=all_text[:2000],
            )
        except Exception as e:
            logger.error(f"Excel Method 1 (Grid) failed: {e}")
            return SingleExtractorOutput(
                method="excel_grid", success=False, error_message=str(e)
            )

    @classmethod
    async def extract_excel_method_2_table(
        cls,
        file_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> SingleExtractorOutput:
        """
        Method 2: Excel Tabular Header & Row mapper.

        Resolution priority: AI → static alias → regex.
        """
        try:
            rows = load_spreadsheet_rows(file_path, master_type=master_type)
            all_text = "\n".join(" ".join(c for c in r if c) for r in rows)
            detected_type = master_type or detect_master_type_from_text(all_text)
            patterns = (
                ITEM_FIELD_PATTERNS
                if detected_type == MasterDataType.ITEM
                else BP_FIELD_PATTERNS
                if detected_type == MasterDataType.BUSINESS_PARTNER
                else WH_FIELD_PATTERNS
            )

            header_idx, header_cells = _find_header_row(rows)
            raw_headers = [c for c in header_cells if c]

            ai_mapping: Optional[Dict[str, str]] = None
            primary_data: Dict[str, Any] = {}
            records: List[Dict[str, Any]] = []

            if raw_headers:
                ai_mapping = await get_ai_column_mapping(
                    raw_headers, master_type=detected_type
                )

            if header_idx >= 0:
                col_index_map = _build_col_index_map(
                    header_cells, ai_mapping or {}
                )
                if col_index_map:
                    data_rows = rows[header_idx + 1:]
                    primary_data, records = parse_spreadsheet_data_with_mapping(
                        data_rows, col_index_map
                    )
                    src = "AI+fuzzy" if ai_mapping else "fuzzy/regex"
                    logger.info(
                        f"[Method 2 Table] {src} mapping used — "
                        f"{len(records)} records parsed."
                    )

            if not records:
                logger.info(
                    "[Method 2 Table] Falling back to regex parse_spreadsheet_data()."
                )
                primary_data, records = parse_spreadsheet_data(rows, patterns)

            normalized = normalization_service.normalize_dict(primary_data)
            return SingleExtractorOutput(
                method="excel_table",
                success=True,
                master_type=detected_type,
                data=normalized,
                records=records,
                raw_text=all_text[:2000],
            )
        except Exception as e:
            logger.error(f"Excel Method 2 (Table) failed: {e}")
            return SingleExtractorOutput(
                method="excel_table", success=False, error_message=str(e)
            )

    @classmethod
    async def extract_excel_method_3_text_layout(
        cls,
        file_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> SingleExtractorOutput:
        """
        Method 3: Excel Serialized Text Layout pattern stream.

        Resolution priority: AI → static alias → regex.
        Text-stream key-value scan also benefits from _fuzzy_match_header().
        """
        try:
            rows = load_spreadsheet_rows(file_path, master_type=master_type)
            all_text = "\n".join(" ".join(c for c in r if c) for r in rows)
            detected_type = master_type or detect_master_type_from_text(all_text)
            patterns = (
                ITEM_FIELD_PATTERNS
                if detected_type == MasterDataType.ITEM
                else BP_FIELD_PATTERNS
                if detected_type == MasterDataType.BUSINESS_PARTNER
                else WH_FIELD_PATTERNS
            )

            header_idx, header_cells = _find_header_row(rows)
            raw_headers = [c for c in header_cells if c]

            ai_mapping: Optional[Dict[str, str]] = None
            primary_data: Dict[str, Any] = {}
            records: List[Dict[str, Any]] = []

            if raw_headers:
                ai_mapping = await get_ai_column_mapping(
                    raw_headers, master_type=detected_type
                )

            if header_idx >= 0:
                col_index_map = _build_col_index_map(
                    header_cells, ai_mapping or {}
                )
                if col_index_map:
                    data_rows = rows[header_idx + 1:]
                    primary_data, records = parse_spreadsheet_data_with_mapping(
                        data_rows, col_index_map
                    )
                    src = "AI+fuzzy" if ai_mapping else "fuzzy/regex"
                    logger.info(
                        f"[Method 3 TextLayout] {src} mapping used — "
                        f"{len(records)} records parsed."
                    )

            if not records:
                logger.info(
                    "[Method 3 TextLayout] Falling back to regex "
                    "parse_spreadsheet_data()."
                )
                primary_data, records = parse_spreadsheet_data(rows, patterns)

            # Build serialized text stream
            lines: List[str] = []
            for r in rows:
                non_empty = [c.strip() for c in r if c.strip()]
                if not non_empty:
                    continue
                if len(non_empty) == 2 and not is_field_label(
                    non_empty[1], patterns
                ):
                    lines.append(f"{non_empty[0]}: {non_empty[1]}")
                else:
                    lines.append(" | ".join(non_empty))

            full_text = "\n".join(lines)
            raw_data: Dict[str, Any] = dict(primary_data)

            # Key-value text stream scan fallback (only when no tabular records were parsed)
            if not records:
                kv_data = extract_key_values_with_patterns(full_text, patterns)
                for k, v in kv_data.items():
                    if k not in raw_data and not is_field_label(v, patterns):
                        if v.upper() not in ("#REF!", "#N/A", "#VALUE!", "#DIV/0!"):
                            raw_data[k] = v

            normalized = normalization_service.normalize_dict(raw_data)
            return SingleExtractorOutput(
                method="excel_text_layout",
                success=True,
                master_type=detected_type,
                data=normalized,
                records=records,
                raw_text=full_text[:2000],
            )
        except Exception as e:
            logger.error(f"Excel Method 3 (Text Layout) failed: {e}")
            return SingleExtractorOutput(
                method="excel_text_layout",
                success=False,
                error_message=str(e),
            )

    @classmethod
    async def extract_all(
        cls,
        file_path: str,
        master_type: Optional[MasterDataType] = None,
    ) -> List[SingleExtractorOutput]:
        """
        Run 3 independent extractors concurrently.
        Selects PDF or Excel/CSV engines based on file extension.
        """
        ext = Path(file_path).suffix.lower()
        if ext in [".xlsx", ".xls", ".csv", ".xlsm"]:
            res1, res2, res3 = await asyncio.gather(
                cls.extract_excel_method_1_grid(file_path, master_type),
                cls.extract_excel_method_2_table(file_path, master_type),
                cls.extract_excel_method_3_text_layout(file_path, master_type),
            )
            return [res1, res2, res3]
        else:
            res1 = cls.extract_method_1_pymupdf(file_path, master_type)
            res2 = cls.extract_method_2_pdfplumber(file_path, master_type)
            res3 = cls.extract_method_3_ocr_or_layout(file_path, master_type)
            return [res1, res2, res3]


extraction_service = MultiMethodExtractor()