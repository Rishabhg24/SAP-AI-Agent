"""
Normalization Layer for Master Data attributes.
Standardizes booleans, whitespace, dates, numbers, and primary key casing.
"""
from datetime import datetime
import re
import unicodedata
from typing import Any, Dict, Optional

# Standard boolean mappings
TRUE_VALUES = {"true", "yes", "y", "1", "t", "tyes", "active"}
FALSE_VALUES = {"false", "no", "n", "0", "f", "tno", "inactive"}

# Primary key codes that should always be strictly stripped and uppercased
UPPERCASE_CODE_FIELDS = {
    "itemcode", "cardcode", "warehousecode", "country", "currency",
    "panno", "pan", "gstno", "gstin", "hsn", "hsncode", "sac"
}

STATE_CODE_MAP = {
    "andhra pradesh": "AP", "arunachal pradesh": "AR", "assam": "AS", "bihar": "BR",
    "chhattisgarh": "CG", "goa": "GA", "gujarat": "GJ", "haryana": "HR",
    "himachal pradesh": "HP", "jharkhand": "JH", "karnataka": "KA", "kerala": "KL",
    "madhya pradesh": "MP", "maharashtra": "MH", "manipur": "MN", "meghalaya": "ML",
    "mizoram": "MZ", "nagaland": "NL", "odisha": "OD", "orissa": "OD",
    "punjab": "PB", "rajasthan": "RJ", "sikkim": "SK", "tamil nadu": "TN",
    "telangana": "TS", "tripura": "TR", "uttar pradesh": "UP", "uttarakhand": "UK",
    "west bengal": "WB", "delhi": "DL", "jammu and kashmir": "JK", "ladakh": "LA",
    "chandigarh": "CH", "puducherry": "PY", "pondicherry": "PY", "new delhi": "DL"
}

class NormalizationService:
    @staticmethod
    def normalize_string(val: str) -> str:
        """Trim whitespace and normalize Unicode NFKC."""
        if not isinstance(val, str):
            val = str(val)
        normalized = unicodedata.normalize("NFKC", val)
        # Clean non-printable characters
        normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", normalized)
        return normalized.strip()

    @staticmethod
    def normalize_boolean(val: Any) -> Optional[bool]:
        """Convert string or numeric representations to canonical Python bool."""
        if isinstance(val, bool):
            return val
        if val is None:
            return None
        s = str(val).strip().lower()
        if s in TRUE_VALUES:
            return True
        if s in FALSE_VALUES:
            return False
        return None

    @staticmethod
    def normalize_number(val: Any) -> Optional[float]:
        """Clean comma thousands separators and return float."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(",", "")
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def normalize_date(val: Any) -> Optional[str]:
        """Attempt normalization of date strings into ISO 8601 (YYYY-MM-DD)."""
        if not val:
            return None
        s = str(val).strip()
        date_formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d.%m.%Y",
            "%b %d, %Y",
            "%B %d, %Y"
        ]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return s

    @staticmethod
    def normalize_phone(val: Any) -> Optional[str]:
        """Clean extra spaces and non-standard symbols in phone numbers while preserving +."""
        if not val:
            return None
        s = str(val).strip()
        cleaned = re.sub(r"[^\d+\-() ]", "", s)
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def normalize_field_value(cls, field_name: str, value: Any) -> Any:
        """Normalize a single field value based on its field name and type."""
        if value is None:
            return None

        fn_lower = field_name.lower()

        # Boolean flags
        if any(b_name in fn_lower for b_name in ["inventoryitem", "salesitem", "purchaseitem", "inactive", "binactivat"]):
            b_val = cls.normalize_boolean(value)
            return b_val if b_val is not None else value

        # Numeric dimensions/weight/integer codes
        if any(num_name in fn_lower for num_name in ["weight", "length", "width", "height", "volume", "itemsgroupcode", "groupcode", "location"]):
            if fn_lower in ["itemcode", "cardcode", "warehousecode"]:
                pass # Primary key strings handled below
            else:
                num_val = cls.normalize_number(value)
                if num_val is not None:
                    return int(num_val) if num_val.is_integer() else num_val

        # Primary codes: uppercase and stripped
        if fn_lower in UPPERCASE_CODE_FIELDS:
            s_val = cls.normalize_string(str(value))
            return s_val.upper()

        # Item Management Method
        if any(m_name in fn_lower for m_name in ["managementmethod", "managemethod"]):
            s = str(value).strip().lower()
            if "serial" in s:
                return "Serial"
            elif "batch" in s:
                return "Batch"
            elif "none" in s:
                return "None"
            return str(value).strip().title()

        # Item Category
        if "itemcategory" in fn_lower or "itemclass" in fn_lower:
            s = str(value).strip().lower()
            if "service" in s or "labor" in s:
                return "Service"
            elif "item" in s:
                return "Item"
            return str(value).strip().title()

        # Material Type
        if "materialtype" in fn_lower or "mattype" in fn_lower:
            s = str(value).strip().lower()
            if s in ["rm", "raw", "raw material"]:
                return "RM"
            elif s in ["fg", "finished", "finished goods"]:
                return "FG"
            elif "capital" in s:
                return "Capital Goods"
            return str(value).strip().upper()

        # Tax Rate
        if "taxrate" in fn_lower or "vatrate" in fn_lower:
            s = str(value).strip().replace("%", "")
            num_val = cls.normalize_number(s)
            return num_val if num_val is not None else value

        # Dates
        if "date" in fn_lower:
            return cls.normalize_date(value)

        # Phone
        if "phone" in fn_lower or "mobile" in fn_lower or "fax" in fn_lower:
            return cls.normalize_phone(value)

        # General strings
        if isinstance(value, str):
            return cls.normalize_string(value)

        return value

    @classmethod
    def normalize_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize all fields within an extracted data dictionary."""
        normalized: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, dict):
                normalized[k] = cls.normalize_dict(v)
            else:
                normalized[k] = cls.normalize_field_value(k, v)
        return normalized

normalization_service = NormalizationService()
