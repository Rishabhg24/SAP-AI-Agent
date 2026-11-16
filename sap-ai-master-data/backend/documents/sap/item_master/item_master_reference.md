# SAP Business One 10.0: Item Master Data Reference (OITM)

## 1. Overview
The Item Master Data entity (`/b1s/v2/Items`) stores inventory, sales, and purchasing definitions for all items, goods, raw materials, and services managed within SAP Business One.

## 2. Mandatory Fields for Item Creation
To successfully create an Item record in SAP Business One via Service Layer, the following properties are strictly required:
1. `ItemCode` (String, max 50 characters):
   - Unique alphanumeric identifier.
   - Case-insensitive in SQL, but uppercase is recommended across all localizations.
   - Cannot contain spaces or special punctuation characters (`/`, `\`, `'`, `"`).
2. `ItemName` (String, max 100 characters):
   - Clear commercial or technical description of the item.
3. `ItemsGroupCode` (Integer):
   - Foreign key referencing `OITB` (Item Groups).
   - Default value in standard demo systems is `100` (Items).

## 3. Essential Boolean Flags
SAP Business One defines three fundamental flags controlling where the item can be used:
- `InventoryItem` ("tYES" / "tNO"): If set to "tYES", the item is physically managed in warehouse stock.
- `SalesItem` ("tYES" / "tNO"): If set to "tYES", the item can be added to sales orders, deliveries, and A/R invoices.
- `PurchaseItem` ("tYES" / "tNO"): If set to "tYES", the item can be added to purchase orders, goods receipts PO, and A/P invoices.

## 4. Units of Measure (UoM) and Dimensions
- `InventoryUOM` (String, max 20 characters): Base unit of inventory, e.g., "PCS", "KG", "BOX", "MTR".
- `SalesUnit` (String, max 20 characters): Unit in sales transactions.
- `PurchaseUnit` (String, max 20 characters): Unit in purchasing transactions.
- Physical attributes:
  * `SalesUnitLength`, `SalesUnitWidth`, `SalesUnitHeight` (Numeric/Float >= 0.0)
  * `SalesUnitVolume` (Numeric/Float >= 0.0)
  * `SalesUnitWeight` (Numeric/Float >= 0.0)
  * `PurchaseUnitWeight` (Numeric/Float >= 0.0)

## 5. Supplementary Identification
- `BarCode` (String, max 100 characters): EAN/UPC barcode representation.
- `ForeignName` (String, max 100 characters): Secondary description (often used for international shipping or export declarations).
- `Manufacturer` (Integer): Code of manufacturer from `OMRC`.

## 6. Service Layer Payload Example
```json
{
  "ItemCode": "ITM-10024",
  "ItemName": "Stainless Steel Hex Bolt M8x40",
  "ItemsGroupCode": 100,
  "InventoryItem": "tYES",
  "SalesItem": "tYES",
  "PurchaseItem": "tYES",
  "InventoryUOM": "PCS",
  "SalesUnit": "PCS",
  "PurchaseUnit": "BOX",
  "SalesUnitWeight": 0.045,
  "BarCode": "8901234567890"
}
```
