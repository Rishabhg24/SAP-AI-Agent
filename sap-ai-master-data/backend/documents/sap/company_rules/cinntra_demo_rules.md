# CINNTRA_DEMO_NEW Company Master Data Governance Rules

## 1. Scope
These policies define the operational master data rules configured for company database `CINNTRA_DEMO_NEW`.

## 2. Mandatory Business Rules
1. Business Partner Email Requirement:
   - For all newly created Business Partners (`cSupplier` or `cCustomer`), `EmailAddress` is considered mandatory by company policy to facilitate automated digital purchase order and invoice transmission.
2. Item Group Standard:
   - If an item group is not specified on the uploaded supplier specification, default `ItemsGroupCode` must be assigned to `100` (Standard Finished / Commercial Items).
3. Primary Code Normalization:
   - All Item Codes, BP Card Codes, and Warehouse Codes must be converted to uppercase.
4. Default Currency:
   - If no currency is defined for a Business Partner, the default operational currency is set to `USD`.
5. Duplicate Guard:
   - No record shall be posted to Service Layer without prior verification against active SAP master data using `$filter`.
