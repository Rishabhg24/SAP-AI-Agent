"""
Generate sample Excel workbooks for testing SAP Master Data extraction.
Creates sample_item.xlsx, sample_supplier.xlsx, and sample_warehouse.xlsx.
"""
from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

def create_item_excel(output_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Item Specification"

    # Header style
    navy_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    regular_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Title
    ws.merge_cells("A1:D1")
    ws["A1"] = "SAP BUSINESS ONE - ITEM MASTER DEFINITION"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30

    # Key-Value Form layout
    data = [
        ("Item Code", "ITM-90042"),
        ("Item Name", "Industrial High-Tensile Steel Fastener M12"),
        ("Item Group", "100"),
        ("Inventory Item", "Yes"),
        ("Sales Item", "Yes"),
        ("Purchase Item", "Yes"),
        ("Inventory UOM", "PCS"),
        ("Sales Unit", "BOX"),
        ("Bar Code", "8904561237890"),
        ("Gross Weight", "0.250")
    ]

    ws["A3"] = "Field Name"
    ws["A3"].font = header_font
    ws["A3"].fill = navy_fill
    ws["B3"] = "Specification Value"
    ws["B3"].font = header_font
    ws["B3"].fill = navy_fill

    for idx, (k, v) in enumerate(data, start=4):
        ws[f"A{idx}"] = k
        ws[f"A{idx}"].font = Font(bold=True)
        ws[f"A{idx}"].border = thin_border
        ws[f"B{idx}"] = v
        ws[f"B{idx}"].font = regular_font
        ws[f"B{idx}"].border = thin_border

    # Also add a second sheet with Tabular format
    ws_tab = wb.create_sheet(title="Tabular Export")
    headers = [k for k, _ in data]
    values = [v for _, v in data]

    ws_tab.append(headers)
    for col in range(1, len(headers) + 1):
        cell = ws_tab.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = navy_fill
    ws_tab.append(values)
    for col in range(1, len(values) + 1):
        cell = ws_tab.cell(row=2, column=col)
        cell.font = regular_font
        cell.border = thin_border

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 45

    wb.save(output_path)
    wb.close()
    print(f"Created sample Item Excel at: {output_path}")

def create_bp_excel(output_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Supplier Onboarding"

    green_fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="065F46")
    regular_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws.merge_cells("A1:D1")
    ws["A1"] = "SAP BUSINESS ONE - BUSINESS PARTNER MASTER"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30

    data = [
        ("Vendor Code", "V10048"),
        ("Company Name", "Apex Fasteners Global Corp"),
        ("Partner Type", "Supplier"),
        ("Telephone", "+1-800-555-0199"),
        ("Email Address", "billing@apexfasteners.com"),
        ("Street Address", "742 Evergreen Industrial Parkway"),
        ("Tax ID", "94-3829104"),
        ("Currency", "USD")
    ]

    ws["A3"] = "Master Attribute"
    ws["A3"].font = header_font
    ws["A3"].fill = green_fill
    ws["B3"] = "Partner Value"
    ws["B3"].font = header_font
    ws["B3"].fill = green_fill

    for idx, (k, v) in enumerate(data, start=4):
        ws[f"A{idx}"] = k
        ws[f"A{idx}"].font = Font(bold=True)
        ws[f"A{idx}"].border = thin_border
        ws[f"B{idx}"] = v
        ws[f"B{idx}"].font = regular_font
        ws[f"B{idx}"].border = thin_border

    # Tabular sheet
    ws_tab = wb.create_sheet(title="Tabular Export")
    ws_tab.append([k for k, _ in data])
    for col in range(1, len(data) + 1):
        cell = ws_tab.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = green_fill
    ws_tab.append([v for _, v in data])
    for col in range(1, len(data) + 1):
        cell = ws_tab.cell(row=2, column=col)
        cell.font = regular_font
        cell.border = thin_border

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 45

    wb.save(output_path)
    wb.close()
    print(f"Created sample Business Partner Excel at: {output_path}")

def create_warehouse_excel(output_path: str):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Warehouse Setup"

    amber_fill = PatternFill(start_color="92400E", end_color="92400E", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="92400E")
    regular_font = Font(name="Calibri", size=11)
    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws.merge_cells("A1:D1")
    ws["A1"] = "SAP BUSINESS ONE - WAREHOUSE DEFINITION"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 30

    data = [
        ("Warehouse Code", "WH02"),
        ("Warehouse Name", "West Coast Logistics Fulfillment Hub"),
        ("Facility Street", "1200 Pacific Marine Drive"),
        ("City", "Seattle"),
        ("Country", "US"),
        ("Inactive", "No"),
        ("Bin Locations", "No")
    ]

    ws["A3"] = "Warehouse Attribute"
    ws["A3"].font = header_font
    ws["A3"].fill = amber_fill
    ws["B3"] = "Setup Value"
    ws["B3"].font = header_font
    ws["B3"].fill = amber_fill

    for idx, (k, v) in enumerate(data, start=4):
        ws[f"A{idx}"] = k
        ws[f"A{idx}"].font = Font(bold=True)
        ws[f"A{idx}"].border = thin_border
        ws[f"B{idx}"] = v
        ws[f"B{idx}"].font = regular_font
        ws[f"B{idx}"].border = thin_border

    # Tabular sheet
    ws_tab = wb.create_sheet(title="Tabular Export")
    ws_tab.append([k for k, _ in data])
    for col in range(1, len(data) + 1):
        cell = ws_tab.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = amber_fill
    ws_tab.append([v for _, v in data])
    for col in range(1, len(data) + 1):
        cell = ws_tab.cell(row=2, column=col)
        cell.font = regular_font
        cell.border = thin_border

    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 45

    wb.save(output_path)
    wb.close()
    print(f"Created sample Warehouse Excel at: {output_path}")

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "uploads"
    out_dir.mkdir(parents=True, exist_ok=True)
    create_item_excel(str(out_dir / "sample_item.xlsx"))
    create_bp_excel(str(out_dir / "sample_supplier.xlsx"))
    create_warehouse_excel(str(out_dir / "sample_warehouse.xlsx"))
