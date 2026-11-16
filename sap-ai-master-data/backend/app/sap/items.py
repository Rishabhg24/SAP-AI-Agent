"""
SAP Service Layer operations for Items (OITM).
Strictly calls /b1s/v2/Items. No direct SQL.
"""
from typing import Any, Dict, Optional
from app.models.item import ItemMasterCreate
from app.sap.client import sap_client
from app.utils.logging import logger

class SAPItemsService:
    @staticmethod
    async def check_item_exists(item_code: str) -> bool:
        """Check if item code already exists using $filter."""
        try:
            params = {
                "$select": "ItemCode",
                "$filter": f"ItemCode eq '{item_code}'"
            }
            res = await sap_client.get("Items", params=params)
            value_list = res.get("value", [])
            return len(value_list) > 0
        except Exception as e:
            logger.warning(f"Error checking item existence for {item_code}: {e}")
            return False

    @staticmethod
    async def create_item(item_model: ItemMasterCreate) -> Dict[str, Any]:
        """Send POST /b1s/v2/Items with verified payload."""
        payload = item_model.to_service_layer_payload()
        return await sap_client.post("Items", payload)

    @staticmethod
    async def get_item(item_code: str) -> Optional[Dict[str, Any]]:
        """Retrieve single item by ItemCode."""
        try:
            res = await sap_client.get("Items", key=item_code)
            return res if res else None
        except Exception as e:
            logger.error(f"Failed to get item {item_code}: {e}")
            return None

    @staticmethod
    async def update_item(item_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send PATCH /b1s/v2/Items('ItemCode') with updated fields."""
        return await sap_client.patch("Items", item_code, payload)

