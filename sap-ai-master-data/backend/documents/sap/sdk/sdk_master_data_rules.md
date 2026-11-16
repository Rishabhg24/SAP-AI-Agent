# SAP Business One SDK & Metadata Rules

## 1. Object Model & Technical Metadata
SAP Business One DI-API and Service Layer enforce strict architectural rules for data integrity across all core business objects.

### Field Constraints
| Entity | Key Field | Max Length | Supported Characters | Required |
| :--- | :--- | :--- | :--- | :--- |
| Item Master (OITM) | `ItemCode` | 50 | Alphanumeric, hyphen, underscore | Yes |
| Business Partner (OCRD) | `CardCode` | 15 | Alphanumeric, hyphen, underscore | Yes |
| Warehouse (OWHS) | `WarehouseCode` | 8 | Alphanumeric, hyphen | Yes |

### General Rules for Master Data Validation
1. Case Sensitivity:
   - Primary key codes (`ItemCode`, `CardCode`, `WarehouseCode`) should always be normalized to uppercase to prevent collation mismatch across localized database engines (SAP HANA / Microsoft SQL Server).
2. Space Trimming:
   - Leading and trailing whitespace must be deterministically stripped from text attributes prior to API dispatch.
3. Boolean Representation:
   - Service Layer expects string representations `"tYES"` or `"tNO"` for standard boolean properties (e.g. `InventoryItem`, `SalesItem`, `PurchaseItem`, `Inactive`, `BinActivat`).
4. Read-Only Fields:
   - Properties such as `OnHand`, `IsCommited`, `OnOrder`, `CreationDate`, `UserSign` are system-computed and must NOT be included in creation payloads.
