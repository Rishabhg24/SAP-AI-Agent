"""
Warehouse Pydantic models conforming to SAP Business One Service Layer Warehouses schema.
"""
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

class WarehouseCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    WarehouseCode: str = Field(
        default="WH01",
        min_length=1,
        max_length=8,
        description="Warehouse code (max 8 chars in SAP)"
    )
    WarehouseName: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Warehouse description/name (max 100 chars in SAP)"
    )
    Location: Optional[Union[int, str]] = Field(default=1, description="Location code or name (OLCT)")
    Address: Optional[str] = Field(default=None, max_length=200, description="Physical street address")
    Inactive: bool = Field(default=False, description="Whether warehouse is inactive")
    WarehouseType: Optional[str] = Field(default="Standard", max_length=20)
    BinActivat: bool = Field(default=False, description="Enable Bin locations ('tYES'/'tNO')")
    Street: Optional[str] = Field(default=None, max_length=100)
    City: Optional[str] = Field(default=None, max_length=100)
    Country: Optional[str] = Field(default="IN", max_length=3)
    extra_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("WarehouseCode", mode="before")
    @classmethod
    def clean_warehouse_code(cls, v: Any) -> str:
        cleaned = str(v or "").strip().upper()
        if not cleaned:
            cleaned = "WH01"
        return cleaned[:8]

    @field_validator("WarehouseName", mode="before")
    @classmethod
    def clean_warehouse_name(cls, v: Any) -> Optional[str]:
        cleaned = str(v or "").strip()
        if not cleaned:
            return None
        return cleaned[:100]

    def to_service_layer_payload(self) -> Dict[str, Any]:
        """Convert to official SAP Business One Service Layer JSON format."""
        loc_val = 1
        if self.Location is not None:
            if isinstance(self.Location, int):
                loc_val = self.Location
            elif str(self.Location).isdigit():
                loc_val = int(self.Location)

        wh_code = (self.WarehouseCode or "WH01")[:8]
        wh_name = (self.WarehouseName or f"Warehouse {wh_code}")[:100]

        payload: Dict[str, Any] = {
            "WarehouseCode": wh_code,
            "WarehouseName": wh_name,
            "Location": loc_val,
        }
        if self.Inactive:
            payload["Inactive"] = "tYES"
        street_val = self.Street or self.Address
        if street_val:
            payload["Street"] = str(street_val)[:100]
        if self.City:
            payload["City"] = str(self.City)[:100]

        # Include all User-Defined Fields (UDFs starting with U_ or custom extra_fields)
        all_extras: Dict[str, Any] = {}
        if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
            all_extras.update(self.__pydantic_extra__)
        if self.extra_fields and isinstance(self.extra_fields, dict):
            all_extras.update(self.extra_fields)

        for k, v in all_extras.items():
            if str(k).startswith("U_") and k not in payload and v is not None and v != "":
                payload[k] = v

        return payload

