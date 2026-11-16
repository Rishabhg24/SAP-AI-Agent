"""
Duplicate Detection Service.
Performs non-destructive OData filter queries against SAP Service Layer prior to posting.
"""
from typing import Any, Dict, Optional, Tuple
from app.models.extraction import MasterDataType
from app.sap.business_partners import SAPBusinessPartnersService
from app.sap.items import SAPItemsService
from app.sap.warehouses import SAPWarehousesService
from app.utils.logging import logger

class DuplicateService:
    @staticmethod
    async def check_duplicate(master_type: MasterDataType, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if primary key code already exists in SAP.
        Returns: (is_duplicate: bool, friendly_message: Optional[str])
        """
        if master_type == MasterDataType.ITEM:
            item_code = data.get("ItemCode")
            if not item_code:
                return False, None
            exists = await SAPItemsService.check_item_exists(str(item_code).strip())
            if exists:
                return True, f"An Item with code '{item_code}' already exists in SAP."

        elif master_type == MasterDataType.BUSINESS_PARTNER:
            card_code = data.get("CardCode")
            if not card_code:
                return False, None
            exists = await SAPBusinessPartnersService.check_card_exists(str(card_code).strip())
            if exists:
                return True, f"A Business Partner with code '{card_code}' already exists in SAP."

        elif master_type == MasterDataType.WAREHOUSE:
            wh_code = data.get("WarehouseCode")
            if not wh_code:
                return False, None
            exists = await SAPWarehousesService.check_warehouse_exists(str(wh_code).strip())
            if exists:
                return True, f"A Warehouse with code '{wh_code}' already exists in SAP."

        return False, None

duplicate_service = DuplicateService()
