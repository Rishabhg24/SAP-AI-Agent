"""
SAP Service Layer operations for Business Partners (OCRD).
Strictly calls /b1s/v2/BusinessPartners. No direct SQL.
"""
from typing import Any, Dict, Optional
from app.models.business_partner import BusinessPartnerCreate
from app.sap.client import sap_client
from app.utils.logging import logger

class SAPBusinessPartnersService:
    @staticmethod
    async def check_card_exists(card_code: str) -> bool:
        """Check if CardCode already exists using $filter."""
        try:
            params = {
                "$select": "CardCode",
                "$filter": f"CardCode eq '{card_code}'"
            }
            res = await sap_client.get("BusinessPartners", params=params)
            value_list = res.get("value", [])
            return len(value_list) > 0
        except Exception as e:
            logger.warning(f"Error checking Business Partner existence for {card_code}: {e}")
            return False

    @staticmethod
    async def create_business_partner(bp_model: BusinessPartnerCreate) -> Dict[str, Any]:
        """Send POST /b1s/v2/BusinessPartners with verified payload."""
        payload = bp_model.to_service_layer_payload()
        return await sap_client.post("BusinessPartners", payload)

    @staticmethod
    async def get_business_partner(card_code: str) -> Optional[Dict[str, Any]]:
        """Retrieve single Business Partner by CardCode."""
        try:
            res = await sap_client.get("BusinessPartners", key=card_code)
            return res if res else None
        except Exception as e:
            logger.error(f"Failed to get Business Partner {card_code}: {e}")
            return None

    @staticmethod
    async def update_business_partner(card_code: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send PATCH /b1s/v2/BusinessPartners('CardCode') with updated fields."""
        return await sap_client.patch("BusinessPartners", card_code, payload)

