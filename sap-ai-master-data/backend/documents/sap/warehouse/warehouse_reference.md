# SAP Business One 10.0: Warehouse Master Data Reference (OWHS)

## 1. Overview
The Warehouse entity (`/b1s/v2/Warehouses`) records storage facilities, logistics centers, virtual drop-ship locations, and consignment depots within SAP Business One.

## 2. Mandatory Fields for Warehouse Creation
1. `WarehouseCode` (String, maximum 8 characters):
   - Strict length limit: must NOT exceed 8 characters in SAP Business One.
   - Unique alphanumeric code (e.g. `WH01`, `CENTRAL`, `NORTH01`).
   - Uppercase recommended.
2. `WarehouseName` (String, maximum 100 characters):
   - Clear name or location description of the warehouse facility.

## 3. Configuration Properties
- `Location` (Integer): Foreign key referencing warehouse locations table (`OLCT`).
- `Inactive` ("tYES" / "tNO"): Indicates whether the warehouse is locked against new inventory movements. Default is "tNO".
- `BinActivat` ("tYES" / "tNO"): Activates bin location management sublevels. Default is "tNO".
- `WarehouseType` (String, max 20 characters): Type classification.
- `Street` (String, max 100 characters): Physical road or logistics park.
- `City` (String, max 100 characters): Municipality or city.
- `Country` (String, max 3 characters): ISO 3166-1 alpha-2 or alpha-3 country code.

## 4. Service Layer Payload Example
```json
{
  "WarehouseCode": "WH-EAST",
  "WarehouseName": "Eastern Regional Distribution Center",
  "Inactive": "tNO",
  "BinActivat": "tNO",
  "Street": "88 Logistics Boulevard",
  "City": "Philadelphia",
  "Country": "US"
}
```
