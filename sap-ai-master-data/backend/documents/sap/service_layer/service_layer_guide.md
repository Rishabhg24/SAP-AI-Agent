# Working with SAP Business One Service Layer (Version 10.0)

## 1. Overview and Architecture
The SAP Business One Service Layer is a modern REST-based API providing high-performance access to SAP Business One core objects. The Service Layer is built on OData v3/v4 protocol standards and uses HTTP methods for CRUD operations.

Base URI format:
`https://<server>:<port>/b1s/v2/<EntitySet>`

## 2. Authentication and Session Management
Authentication is conducted via the `/Login` endpoint using JSON credentials:
```http
POST /b1s/v2/Login HTTP/1.1
Content-Type: application/json

{
    "CompanyDB": "CINNTRA_DEMO_NEW",
    "UserName": "Cinntra1",
    "Password": "..."
}
```
Upon successful authentication, the Service Layer returns HTTP 200 with cookies:
- `B1SESSION`: Session token string
- `ROUTEID`: Load balancer routing identifier

All subsequent requests must include these cookies in the HTTP `Cookie` header.

## 3. Core Allowlisted Master Data Entities
The following entity sets represent the authoritative endpoints for master data creation:
- Items: `/b1s/v2/Items` (Corresponds to OITM)
- Business Partners: `/b1s/v2/BusinessPartners` (Corresponds to OCRD)
- Warehouses: `/b1s/v2/Warehouses` (Corresponds to OWHS)

Direct database writes (e.g. `INSERT INTO OITM`) are strictly prohibited by SAP and void database integrity. All master data creation must traverse the Service Layer.

## 4. Querying and Duplicate Verification
The Service Layer supports OData query options to check for duplicate records before creation:
- `$filter`: Filter expressions (e.g. `ItemCode eq 'ITM001'`, `CardCode eq 'V1000'`)
- `$select`: Comma-separated list of properties to retrieve
- `$top` and `$skip`: Pagination controls

Example duplicate check:
`GET /b1s/v2/Items?$select=ItemCode&$filter=ItemCode eq 'ITM001'`

## 5. Error Handling and Status Codes
The Service Layer returns structured JSON error responses:
- `400 Bad Request`: Payload validation errors, invalid enum values, missing required fields.
- `401 Unauthorized`: Session expired or invalid credentials.
- `409 Conflict`: Unique constraint violation or concurrency collision.
- Error Code `-2028`: Record already exists with the given key.
- Error Code `-1004`: General validation failure.
- Error Code `-5002`: Invalid foreign key or linked entity reference.
