# SAP Business One 10.0: Business Partner Master Data Reference (OCRD)

## 1. Overview
The Business Partner entity (`/b1s/v2/BusinessPartners`) represents external legal entities with whom the company transacts: Customers, Vendors/Suppliers, and Leads.

## 2. Mandatory Fields for Business Partner Creation
The following properties are required by the Service Layer:
1. `CardCode` (String, maximum 15 characters):
   - Strict length limit: must NOT exceed 15 characters in SAP Business One.
   - Unique identifier across all business partners.
   - Recommended convention: Alphanumeric prefix denoting type (e.g. `V1001` for vendor, `C1001` for customer).
2. `CardName` (String, maximum 100 characters):
   - Full registered company name or individual legal name.
3. `CardType` (Enumeration String):
   - Authoritative SAP Service Layer enum values:
     * `cCustomer`: Client / Customer receiving goods or services.
     * `cSupplier`: Vendor / Supplier supplying goods or services.
     * `cLid`: Prospective Lead before formal trading.
   - User inputs such as "Vendor" or "Supplier" map to `cSupplier`.

## 3. Communication and Contact Details
- `GroupCode` (Integer): Group classification from `OCRG`. Standard default is `100`.
- `Phone1` (String, max 20 characters): Primary business telephone number.
- `Phone2` (String, max 20 characters): Secondary or mobile contact.
- `EmailAddress` (String, max 100 characters): Valid formatted email address for electronic invoicing and PO dispatch.
- `Address` (String, max 100 characters): Primary street location.
- `FederalTaxID` (String, max 32 characters): Government tax registration number (GSTIN, Tax ID, VAT, or EIN).
- `Currency` (String, 3 characters): ISO currency code (e.g., "USD", "EUR", "GBP", "INR") or "##" for all currencies.

## 4. Addresses Collection (BPAddresses)
Business partners can have multiple physical addresses specified in the `BPAddresses` array:
- `AddressName`: Friendly label (e.g. "Headquarters", "Billing Office").
- `Street`, `City`, `ZipCode`, `Country`: Address components.
- `AddressType`: `bo_BillTo` (Bill To) or `bo_ShipTo` (Ship To).

## 5. Service Layer Payload Example
```json
{
  "CardCode": "S-90042",
  "CardName": "Apex Precision Components Ltd",
  "CardType": "cSupplier",
  "GroupCode": 100,
  "Phone1": "+1-555-0199",
  "EmailAddress": "procurement@apexprecision.com",
  "Address": "450 Industrial Parkway",
  "FederalTaxID": "94-2849102",
  "Currency": "USD"
}
```
