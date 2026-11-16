"""
SAP Service Layer operations for Warehouses (OWHS).
Strictly calls /b1s/v2/Warehouses. No direct SQL.
"""
from typing import Any, Dict, Optional
from app.models.warehouse import WarehouseCreate
from app.sap.client import sap_client
from app.utils.logging import logger

class SAPWarehousesService:
    @staticmethod
    async def check_warehouse_exists(warehouse_code: str) -> bool:
        """Check if WarehouseCode already exists using $filter."""
        try:
            params = {
                "$select": "WarehouseCode",
                "$filter": f"WarehouseCode eq '{warehouse_code}'"
            }
            res = await sap_client.get("Warehouses", params=params)
            value_list = res.get("value", [])
            return len(value_list) > 0
        except Exception as e:
            logger.warning(f"Error checking warehouse existence for {warehouse_code}: {e}")
            return False

    @staticmethod
    async def create_warehouse(wh_model: WarehouseCreate) -> Dict[str, Any]:
        """Send POST /b1s/v2/Warehouses with verified payload."""
        payload = wh_model.to_service_layer_payload()
        return await sap_client.post("Warehouses", payload)

    @staticmethod
    async def get_warehouse(warehouse_code: str) -> Optional[Dict[str, Any]]:
        """Retrieve single warehouse by WarehouseCode."""
        try:
            res = await sap_client.get("Warehouses", key=warehouse_code)
            return res if res else None
        except Exception as e:
            logger.error(f"Failed to get warehouse {warehouse_code}: {e}")
            return None

    @staticmethod
    async def update_warehouse(warehouse_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send PATCH /b1s/v2/Warehouses('WarehouseCode') with updated fields."""
        return await sap_client.patch("Warehouses", warehouse_code, payload)

