"""
Business Partner Pydantic models conforming to SAP Business One Service Layer BusinessPartners schema.
"""
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

class CardTypeEnum(str, Enum):
    CUSTOMER = "cCustomer"
    SUPPLIER = "cSupplier"
    LEAD = "cLid"

class BusinessPartnerCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    CardCode: str = Field(
        default="BP-DEFAULT",
        min_length=1,
        max_length=15,
        description="Unique Business Partner identifier (max 15 chars in SAP)"
    )
    CardName: str = Field(
        default="Business Partner",
        min_length=1,
        max_length=100,
        description="Business Partner Name (max 100 chars in SAP)"
    )
    CardType: CardTypeEnum = Field(
        default=CardTypeEnum.SUPPLIER,
        description="Type: cCustomer, cSupplier, or cLid"
    )
    GroupCode: int = Field(default=100, description="BP Group Code (OCRG)")
    Series: Optional[int] = Field(default=None, description="Numbering Series in SAP")
    Phone1: Optional[str] = Field(default=None, max_length=50)
    Phone2: Optional[str] = Field(default=None, max_length=50)
    EmailAddress: Optional[str] = Field(default=None, max_length=100)
    Address: Optional[str] = Field(default=None, max_length=200)
    FederalTaxID: Optional[str] = Field(default=None, max_length=32)
    Currency: Optional[str] = Field(default="INR", max_length=3)
    # Additional Mandatory Master Data Attributes
    TaxDetails: Optional[str] = Field(default=None, description="Tax Structure / Group e.g. GST 18%, IGST")
    PaymentTerms: Optional[Union[str, int]] = Field(default=None, description="Payment Terms e.g. Net 30, Cash")
    ControlAccount: Optional[str] = Field(default=None, description="GL Control Account e.g. 211000")
    GSTNo: Optional[str] = Field(default=None, description="GSTIN Number (15 chars) if party registered")
    PANNo: Optional[str] = Field(default=None, description="PAN Number (10 chars)")
    GSTRegStatus: Optional[str] = Field(default="Registered", description="Registration Status: Registered or Unregistered")
    City: Optional[str] = Field(default=None, max_length=100)
    State: Optional[str] = Field(default=None, max_length=100)
    ZipCode: Optional[str] = Field(default=None, max_length=20)
    Country: Optional[str] = Field(default="IN", max_length=10)
    BPAddresses: List[Dict[str, Any]] = Field(default_factory=list)
    ContactEmployees: List[Dict[str, Any]] = Field(default_factory=list)
    BPFiscalTaxIDCollection: List[Dict[str, Any]] = Field(default_factory=list)
    extra_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("CardCode", mode="before")
    @classmethod
    def clean_card_code(cls, v: Any) -> str:
        cleaned = str(v or "").strip().upper()
        if not cleaned:
            cleaned = "BP-DEFAULT"
        return cleaned[:15]

    @field_validator("CardName", mode="before")
    @classmethod
    def clean_card_name(cls, v: Any) -> str:
        cleaned = str(v or "").strip()
        if not cleaned:
            return "Business Partner"
        return cleaned[:100]

    @field_validator("CardType", mode="before")
    @classmethod
    def normalize_card_type(cls, v: Any) -> CardTypeEnum:
        if isinstance(v, CardTypeEnum):
            return v
        s = str(v or "").strip().lower()
        if s in ["ccustomer", "customer", "cust", "c", "client"]:
            return CardTypeEnum.CUSTOMER
        elif s in ["csupplier", "supplier", "vendor", "supp", "s", "v"]:
            return CardTypeEnum.SUPPLIER
        elif s in ["clid", "lead", "l"]:
            return CardTypeEnum.LEAD
        return CardTypeEnum.SUPPLIER

    @field_validator("EmailAddress", mode="before")
    @classmethod
    def validate_email(cls, v: Any) -> Optional[str]:
        if not v:
            return None
        cleaned = str(v).strip()
        # Strictly ignore if invalid or looks like concatenated column headers
        if not cleaned or "@" not in cleaned or len(cleaned.split("@")) != 2 or "|" in cleaned:
            return None
        return cleaned[:100]

    def to_service_layer_payload(self) -> Dict[str, Any]:
        """Convert to official SAP Business One Service Layer JSON format."""
        group_code = self.GroupCode
        if group_code is None or (self.CardType == CardTypeEnum.SUPPLIER and group_code == 100):
            group_code = 101 if self.CardType == CardTypeEnum.SUPPLIER else 100

        gst_str = str(self.GSTNo or self.FederalTaxID or "").strip().upper()
        pan_str = str(self.PANNo or "").strip().upper()
        if not pan_str and len(gst_str) == 15 and gst_str[:2].isdigit():
            pan_str = gst_str[2:12]
        if not pan_str or len(pan_str) != 10:
            pan_str = "ABCDE1234F"

        code_str = str(self.CardCode or "BP-DEFAULT")[:15]
        name_str = str(self.CardName or f"BP {code_str}")[:100]

        pay_terms = -1 if self.CardType == CardTypeEnum.CUSTOMER else 2

        payload: Dict[str, Any] = {
            "CardCode": code_str,
            "CardName": name_str,
            "CardType": self.CardType.value,
            "GroupCode": group_code,
            "PayTermsGrpCode": pay_terms,
            "Currency": self.Currency or "INR",
        }

        # Include custom User-Defined Fields only if explicitly requested
        if getattr(self, "U_VSG", None):
            payload["U_VSG"] = self.U_VSG
        if getattr(self, "U_panno", None):
            payload["U_panno"] = self.U_panno

        # Set numbering series if provided or apply standard SAP defaults
        if self.Series is not None:
            payload["Series"] = self.Series
        else:
            if self.CardType == CardTypeEnum.SUPPLIER:
                payload["Series"] = 2
            else:
                payload["Series"] = 86

        if self.Phone1 and isinstance(self.Phone1, (str, int)):
            p1_str = str(self.Phone1).strip()
            if p1_str and "|" not in p1_str:
                payload["Phone1"] = p1_str[:20]
        if self.Phone2 and isinstance(self.Phone2, (str, int)):
            p2_str = str(self.Phone2).strip()
            if p2_str and "|" not in p2_str:
                payload["Phone2"] = p2_str[:20]
        if self.EmailAddress and "@" in str(self.EmailAddress):
            payload["EmailAddress"] = str(self.EmailAddress)[:100]
        if self.Address and isinstance(self.Address, str) and self.Address.strip():
            payload["Address"] = str(self.Address).strip()[:200]

        if gst_str and len(gst_str) == 15:
            payload["FederalTaxID"] = gst_str

        state_map = {
            "DELHI": "DL", "DL": "DL",
            "MAHARASHTRA": "MH", "MH": "MH",
            "KARNATAKA": "KA", "KA": "KA",
            "TAMIL NADU": "TN", "TAMILNADU": "TN", "TN": "TN",
            "UTTAR PRADESH": "UP", "UP": "UP",
            "GUJARAT": "GJ", "GJ": "GJ",
            "HARYANA": "HR", "HR": "HR",
            "WEST BENGAL": "WB", "WB": "WB",
            "RAJASTHAN": "RJ", "RJ": "RJ",
            "TELANGANA": "TG", "TG": "TG",
            "ANDHRA PRADESH": "AP", "AP": "AP",
            "MADHYA PRADESH": "MP", "MP": "MP",
            "PUNJAB": "PB", "PB": "PB",
            "UTTARAKHAND": "UK", "UK": "UK",
            "KERALA": "KL", "KL": "KL",
            "ODISHA": "OD", "OD": "OD", "ORISSA": "OD",
            "BIHAR": "BR", "BR": "BR",
            "JHARKHAND": "JH", "JH": "JH",
            "CHHATTISGARH": "CG", "CG": "CG",
            "ASSAM": "AS", "AS": "AS",
            "HIMACHAL PRADESH": "HP", "HP": "HP",
            "JAMMU AND KASHMIR": "JK", "JK": "JK",
            "GOA": "GA", "GA": "GA",
            "CHANDIGARH": "CH", "CH": "CH",
        }

        # Resolve state code
        raw_state = str(self.State or "").strip().upper()
        resolved_state = state_map.get(raw_state, "DL")

        # Configure Addresses tab in SAP
        if self.BPAddresses and len(self.BPAddresses) > 0:
            formatted_addrs = []
            for addr in self.BPAddresses:
                item = dict(addr)
                if not item.get("State"):
                    item["State"] = resolved_state
                else:
                    item["State"] = state_map.get(str(item["State"]).strip().upper(), resolved_state)
                if not item.get("Country"):
                    item["Country"] = "IN"
                formatted_addrs.append(item)
            payload["BPAddresses"] = formatted_addrs
        else:
            street_val = str(self.Address or "")[:100]
            city_val = str(self.City or "")[:100]
            zip_val = str(self.ZipCode or "")[:20]
            payload["BPAddresses"] = [
                {
                    "AddressName": "Bill To",
                    "Street": street_val,
                    "City": city_val,
                    "ZipCode": zip_val,
                    "Country": "IN",
                    "State": resolved_state,
                    "AddressType": "bo_BillTo"
                },
                {
                    "AddressName": "Ship To",
                    "Street": street_val,
                    "City": city_val,
                    "ZipCode": zip_val,
                    "Country": "IN",
                    "State": resolved_state,
                    "AddressType": "bo_ShipTo"
                }
            ]

        # Add PAN & Deductee Ref No to BPFiscalTaxIDCollection for India SAP compliance
        payload["BPFiscalTaxIDCollection"] = [
            {"Address": "", "TaxId0": pan_str, "AddrType": "bo_ShipTo", "TaxId12": f"{code_str}/DEFAULT"},
            {"Address": "Bill To", "TaxId0": pan_str, "AddrType": "bo_BillTo", "TaxId12": f"{code_str}/BILL"},
            {"Address": "Ship To", "TaxId0": pan_str, "AddrType": "bo_ShipTo", "TaxId12": f"{code_str}/SHIP"}
        ]

        # ONLY include verified custom fields (starting with U_) to prevent SAP -1000 invalid property errors
        all_extras: Dict[str, Any] = {}
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            all_extras.update(self.__pydantic_extra__)
        if self.extra_fields and isinstance(self.extra_fields, dict):
            all_extras.update(self.extra_fields)

        for k, v in all_extras.items():
            if str(k).startswith("U_") and k not in payload and v is not None and v != "":
                payload[k] = v

        return payload


