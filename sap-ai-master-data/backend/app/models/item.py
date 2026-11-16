"""
Item Master Pydantic models conforming to SAP Business One Service Layer Item schema.
"""
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ItemMasterCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    ItemCode: str = Field(
        default="ITM-DEFAULT",
        min_length=1,
        max_length=50,
        description="Unique identifier for the item (max 50 chars in SAP)"
    )
    ItemName: str = Field(
        default="Item Description",
        min_length=1,
        max_length=100,
        description="Description/name of the item (max 100 chars in SAP)"
    )
    ItemsGroupCode: int = Field(
        default=100,
        description="Foreign key to item group (OITB)"
    )
    InventoryItem: bool = Field(default=True, description="Whether item is kept in inventory ('tYES'/'tNO' in SAP)")
    SalesItem: bool = Field(default=True, description="Whether item can be sold")
    PurchaseItem: bool = Field(default=True, description="Whether item can be purchased")
    InventoryUOM: Optional[str] = Field(default="PCS", max_length=20, description="Inventory Unit of Measure")
    SalesUnit: Optional[str] = Field(default=None, max_length=20, description="Sales Unit of Measure")
    PurchaseUnit: Optional[str] = Field(default=None, max_length=20, description="Purchase Unit of Measure")
    SalesUnitLength: Optional[float] = Field(default=None, ge=0.0)
    SalesUnitWidth: Optional[float] = Field(default=None, ge=0.0)
    SalesUnitHeight: Optional[float] = Field(default=None, ge=0.0)
    SalesUnitVolume: Optional[float] = Field(default=None, ge=0.0)
    SalesUnitWeight: Optional[float] = Field(default=None, ge=0.0)
    PurchaseUnitWeight: Optional[float] = Field(default=None, ge=0.0)
    BarCode: Optional[str] = Field(default=None, max_length=100)
    Manufacturer: Optional[int] = Field(default=None)
    ForeignName: Optional[str] = Field(default=None, max_length=100)
    # Additional Mandatory Master Data Attributes
    ItemType: Optional[str] = Field(default="Inventory/Sales/Purchase", description="Item Type e.g. Inventory/Sales/Purchase")
    TaxRate: Optional[Union[float, str]] = Field(default=None, description="Tax Rate (e.g. 18% or 18.0)")
    ItemManagementMethod: Optional[str] = Field(default="None", description="Management Method: Serial, Batch, or None")
    ItemCategory: Optional[str] = Field(default="Item", description="Item Category: Service or Item")
    MaterialType: Optional[str] = Field(default=None, description="Material Type: RM, FG, or Capital Goods")
    HSN: Optional[str] = Field(default=None, description="Harmonized System of Nomenclature / SAC code")
    TaxCategory: Optional[str] = Field(default=None, description="Tax Category e.g. Taxable, Exempted, Nil Rated")
    extra_fields: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("ItemCode", mode="before")
    @classmethod
    def clean_item_code(cls, v: Any) -> str:
        cleaned = str(v or "").strip().upper()
        if not cleaned:
            cleaned = "ITM-DEFAULT"
        return cleaned[:50]

    @field_validator("ItemName", mode="before")
    @classmethod
    def clean_item_name(cls, v: Any) -> str:
        cleaned = str(v or "").strip()
        if not cleaned:
            return "Item Description"
        return cleaned[:100]

    @field_validator("ItemsGroupCode", mode="before")
    @classmethod
    def clean_group_code(cls, v: Any) -> int:
        if isinstance(v, int):
            return v
        try:
            return int(str(v).strip())
        except (ValueError, TypeError):
            return 100

    def to_service_layer_payload(self) -> Dict[str, Any]:
        """Convert to official SAP Business One Service Layer JSON format."""
        inv_flag = self.InventoryItem
        sales_flag = self.SalesItem
        purch_flag = self.PurchaseItem

        # Infer flags from ItemType if explicitly given
        if self.ItemType:
            it_lower = str(self.ItemType).lower()
            if "inventory" in it_lower or "all" in it_lower:
                inv_flag = True
            if "sales" in it_lower or "all" in it_lower:
                sales_flag = True
            if "purchase" in it_lower or "all" in it_lower:
                purch_flag = True

        payload: Dict[str, Any] = {
            "ItemCode": self.ItemCode[:50],
            "ItemName": self.ItemName[:100],
            "ItemsGroupCode": self.ItemsGroupCode or 100,
            "InventoryItem": "tYES" if inv_flag else "tNO",
            "SalesItem": "tYES" if sales_flag else "tNO",
            "PurchaseItem": "tYES" if purch_flag else "tNO",
        }
        if self.InventoryUOM:
            payload["InventoryUOM"] = str(self.InventoryUOM)[:20]
        if self.SalesUnit:
            payload["SalesUnit"] = str(self.SalesUnit)[:20]
        if self.PurchaseUnit:
            payload["PurchaseUnit"] = str(self.PurchaseUnit)[:20]
        if self.BarCode:
            payload["BarCode"] = str(self.BarCode)[:100]
        if self.ForeignName:
            payload["ForeignName"] = str(self.ForeignName)[:100]

        # Item Management Method
        if self.ItemManagementMethod:
            imm_lower = str(self.ItemManagementMethod).lower()
            if "serial" in imm_lower:
                payload["ManageSerialNumbers"] = "tYES"
                payload["ManageBatchNumbers"] = "tNO"
            elif "batch" in imm_lower:
                payload["ManageSerialNumbers"] = "tNO"
                payload["ManageBatchNumbers"] = "tYES"
            else:
                payload["ManageSerialNumbers"] = "tNO"
                payload["ManageBatchNumbers"] = "tNO"

        # Item Category / Class (itcMaterial vs itcService)
        if self.ItemCategory:
            cat_lower = str(self.ItemCategory).lower()
            payload["ItemClass"] = "itcService" if "service" in cat_lower else "itcMaterial"
        else:
            payload["ItemClass"] = "itcMaterial"

        # HSN
        if self.HSN:
            payload["ChapterID"] = str(self.HSN)[:30]

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

