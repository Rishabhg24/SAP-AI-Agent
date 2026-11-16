import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.models.extraction import MasterDataType
from app.services.validation_service import ValidationService

os.makedirs("sample_data", exist_ok=True)

header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
thin_border = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)
align_left = Alignment(horizontal="left", vertical="center")
align_center = Alignment(horizontal="center", vertical="center")

def format_sheet(ws):
    ws.views.sheetView[0].showGridLines = True
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            cell.border = thin_border
            if cell.row == 1:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = align_center
            else:
                cell.font = Font(name="Calibri", size=10)
                cell.alignment = align_left
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

# 1. ITEM MASTER DATA
items_data = [
    {
        "ItemCode": "ITM-2026-001",
        "ItemName": "Stainless Steel Hex Bolt M10x50",
        "ItemsGroupCode": 100,
        "InventoryUOM": "PCS",
        "ItemType": "Inventory/Sales/Purchase",
        "TaxRate": "18%",
        "ItemManagementMethod": "Batch",
        "ItemCategory": "Item",
        "MaterialType": "RM",
        "HSN": "73181500",
        "TaxCategory": "Taxable",
        "PurchaseUnit": "PCS",
        "SalesUnit": "PCS",
        "BarCode": "8901030865412",
        "PurchaseUnitWeight": 0.25,
        "SalesUnitWeight": 0.25,
    },
    {
        "ItemCode": "ITM-2026-002",
        "ItemName": "High Torque 3-Phase Electric Motor 5HP",
        "ItemsGroupCode": 100,
        "InventoryUOM": "NOS",
        "ItemType": "Inventory/Sales/Purchase",
        "TaxRate": "18%",
        "ItemManagementMethod": "Serial",
        "ItemCategory": "Item",
        "MaterialType": "Capital Goods",
        "HSN": "85015210",
        "TaxCategory": "Taxable",
        "PurchaseUnit": "NOS",
        "SalesUnit": "NOS",
        "BarCode": "8901030865429",
        "PurchaseUnitWeight": 14.5,
        "SalesUnitWeight": 14.5,
    },
    {
        "ItemCode": "ITM-2026-003",
        "ItemName": "Heavy Duty Hydraulic Seal Ring 80mm",
        "ItemsGroupCode": 100,
        "InventoryUOM": "PCS",
        "ItemType": "Inventory/Sales/Purchase",
        "TaxRate": "18%",
        "ItemManagementMethod": "Batch",
        "ItemCategory": "Item",
        "MaterialType": "RM",
        "HSN": "40169320",
        "TaxCategory": "Taxable",
        "PurchaseUnit": "BOX",
        "SalesUnit": "PCS",
        "BarCode": "8901030865436",
        "PurchaseUnitWeight": 0.05,
        "SalesUnitWeight": 0.05,
    },
    {
        "ItemCode": "ITM-2026-004",
        "ItemName": "Precision Deep Groove Ball Bearing 6204-2RS",
        "ItemsGroupCode": 100,
        "InventoryUOM": "PCS",
        "ItemType": "Inventory/Sales/Purchase",
        "TaxRate": "18%",
        "ItemManagementMethod": "Batch",
        "ItemCategory": "Item",
        "MaterialType": "RM",
        "HSN": "84821011",
        "TaxCategory": "Taxable",
        "PurchaseUnit": "PCS",
        "SalesUnit": "PCS",
        "BarCode": "8901030865443",
        "PurchaseUnitWeight": 0.18,
        "SalesUnitWeight": 0.18,
    },
    {
        "ItemCode": "ITM-2026-005",
        "ItemName": "Industrial Lithium Complex EP2 Grease 500g",
        "ItemsGroupCode": 100,
        "InventoryUOM": "KGS",
        "ItemType": "Inventory/Sales/Purchase",
        "TaxRate": "18%",
        "ItemManagementMethod": "Batch",
        "ItemCategory": "Item",
        "MaterialType": "RM",
        "HSN": "27101980",
        "TaxCategory": "Taxable",
        "PurchaseUnit": "KGS",
        "SalesUnit": "KGS",
        "BarCode": "8901030865450",
        "PurchaseUnitWeight": 0.5,
        "SalesUnitWeight": 0.5,
    }
]

# 2. BUSINESS PARTNER DATA
bp_data = [
    {
        "CardCode": "V2026-001",
        "CardName": "Apex Precision Components Pvt Ltd",
        "CardType": "Supplier",
        "Address": "Plot 42, Sector 18, Industrial Area Phase 2, Pune, MH",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "211000",
        "GSTNo": "27AAACA1234A1Z5",
        "PANNo": "AAACA1234A",
        "GSTRegStatus": "Registered",
        "EmailAddress": "accounts@apexprecision.com",
        "Phone1": "+91 98201 12345"
    },
    {
        "CardCode": "V2026-002",
        "CardName": "Global Logistics & Transport Corp",
        "CardType": "Supplier",
        "Address": "12th Floor, Tower B, Cyber City, Gurugram, HR",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "211000",
        "GSTNo": "06AABCG5678B1Z2",
        "PANNo": "AABCG5678B",
        "GSTRegStatus": "Registered",
        "EmailAddress": "billing@globallogistics.in",
        "Phone1": "+91 98111 23456"
    },
    {
        "CardCode": "C2026-001",
        "CardName": "Dynamic Engineering Solutions LLP",
        "CardType": "Customer",
        "Address": "Industrial Complex, Andheri East, Mumbai, MH",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "121000",
        "GSTNo": "27AABCU9603R1ZM",
        "PANNo": "AABCU9603R",
        "GSTRegStatus": "Registered",
        "EmailAddress": "contact@dynamicengineering.com",
        "Phone1": "+91 98222 34567"
    },
    {
        "CardCode": "C2026-002",
        "CardName": "Reliance Polymers & Chemicals Ltd",
        "CardType": "Customer",
        "Address": "Plot 88, Whitefield Tech Zone, Bengaluru, KA",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "121000",
        "GSTNo": "29AABCR8899C1Z1",
        "PANNo": "AABCR8899C",
        "GSTRegStatus": "Registered",
        "EmailAddress": "finance@reliancepolymers.com",
        "Phone1": "+91 98450 45678"
    },
    {
        "CardCode": "V2026-003",
        "CardName": "Vertex Industrial Automation Services",
        "CardType": "Supplier",
        "Address": "54 GIDC Estate, Vatva, Ahmedabad, GJ",
        "TaxDetails": "GST 18%",
        "PaymentTerms": "Net 30",
        "Currency": "INR",
        "ControlAccount": "211000",
        "GSTNo": "24AABCV4321D1Z9",
        "PANNo": "AABCV4321D",
        "GSTRegStatus": "Registered",
        "EmailAddress": "sales@vertexautomation.com",
        "Phone1": "+91 98790 56789"
    }
]

# 3. WAREHOUSE DATA
wh_data = [
    {
        "WarehouseCode": "WH01",
        "WarehouseName": "Central Distribution Hub",
        "Location": "1",
        "Address": "100 Logistics Way, Industrial Park, Mumbai",
        "City": "Mumbai",
        "Country": "IN",
        "WarehouseType": "Standard",
        "Inactive": "No",
        "BinActivat": "No"
    },
    {
        "WarehouseCode": "WH02",
        "WarehouseName": "Raw Material Storage Depot",
        "Location": "1",
        "Address": "Sector 5, IMT Manesar, Gurugram",
        "City": "Gurugram",
        "Country": "IN",
        "WarehouseType": "Standard",
        "Inactive": "No",
        "BinActivat": "No"
    },
    {
        "WarehouseCode": "WH03",
        "WarehouseName": "Finished Goods Hub North",
        "Location": "2",
        "Address": "Survey 45, Chakan MIDC, Pune",
        "City": "Pune",
        "Country": "IN",
        "WarehouseType": "Standard",
        "Inactive": "No",
        "BinActivat": "No"
    },
    {
        "WarehouseCode": "WH04",
        "WarehouseName": "West Regional Logistics Hub",
        "Location": "2",
        "Address": "Electronic City Phase 1, Bengaluru",
        "City": "Bengaluru",
        "Country": "IN",
        "WarehouseType": "Standard",
        "Inactive": "No",
        "BinActivat": "No"
    },
    {
        "WarehouseCode": "WH05",
        "WarehouseName": "South Tech Fulfillment Center",
        "Location": "3",
        "Address": "Sanand Industrial Estate, Ahmedabad",
        "City": "Ahmedabad",
        "Country": "IN",
        "WarehouseType": "Standard",
        "Inactive": "No",
        "BinActivat": "No"
    }
]

# Verify all records deterministically
print("=== VERIFYING TEST RECORDS ===")
for r in items_data:
    res = ValidationService.validate(MasterDataType.ITEM, r)
    assert res.valid, f"Item {r['ItemCode']} failed validation: missing={res.missing_fields}, errors={res.invalid_fields}"
print("[PASS] All 5 Item Master records passed deterministic validation.")

for r in bp_data:
    res = ValidationService.validate(MasterDataType.BUSINESS_PARTNER, r)
    assert res.valid, f"BP {r['CardCode']} failed validation: missing={res.missing_fields}, errors={res.invalid_fields}"
print("[PASS] All 5 Business Partner records passed deterministic validation.")

for r in wh_data:
    res = ValidationService.validate(MasterDataType.WAREHOUSE, r)
    assert res.valid, f"Warehouse {r['WarehouseCode']} failed validation: missing={res.missing_fields}, errors={res.invalid_fields}"
print("[PASS] All 5 Warehouse records passed deterministic validation.")

# Write Individual Excel Files
def write_excel(filename, sheet_name, data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    headers = list(data[0].keys())
    ws.append(headers)
    for row in data:
        ws.append([row.get(h, '') for h in headers])
    format_sheet(ws)
    filepath = os.path.join("sample_data", filename)
    wb.save(filepath)
    print(f"Saved: {filepath}")

write_excel("item_master_template_passed.xlsx", "Item Master", items_data)
write_excel("business_partner_template_passed.xlsx", "Business Partner", bp_data)
write_excel("warehouse_template_passed.xlsx", "Warehouses", wh_data)

# Write All-In-One Excel File with 3 Sheets
wb_all = openpyxl.Workbook()
# Sheet 1: Item Master
ws1 = wb_all.active
ws1.title = "Item Master"
ws1.append(list(items_data[0].keys()))
for row in items_data:
    ws1.append([row.get(h, '') for h in list(items_data[0].keys())])
format_sheet(ws1)

# Sheet 2: Business Partner
ws2 = wb_all.create_sheet(title="Business Partner")
ws2.append(list(bp_data[0].keys()))
for row in bp_data:
    ws2.append([row.get(h, '') for h in list(bp_data[0].keys())])
format_sheet(ws2)

# Sheet 3: Warehouse
ws3 = wb_all.create_sheet(title="Warehouses")
ws3.append(list(wh_data[0].keys()))
for row in wh_data:
    ws3.append([row.get(h, '') for h in list(wh_data[0].keys())])
format_sheet(ws3)

all_path = os.path.join("sample_data", "sap_master_data_all_templates_passed.xlsx")
wb_all.save(all_path)
print(f"Saved All-In-One: {all_path}")
