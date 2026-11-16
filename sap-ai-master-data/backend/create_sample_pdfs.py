import fitz  # PyMuPDF
from pathlib import Path

def create_item_pdf(output_path: str):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 size
    
    # Title
    page.insert_text((50, 60), "MATERIAL SPECIFICATION SHEET", fontsize=16, fontname="helv", color=(0.1, 0.2, 0.4))
    page.insert_text((50, 85), "Document Type: Item Master Definition", fontsize=11, fontname="helv")
    page.insert_text((50, 105), "-" * 60, fontsize=10, fontname="helv")
    
    fields = [
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
    
    y = 135
    for k, v in fields:
        page.insert_text((50, y), f"{k}:", fontsize=10, fontname="helv")
        page.insert_text((180, y), v, fontsize=10, fontname="helv")
        y += 28
        
    doc.save(output_path)
    doc.close()
    print(f"Created sample Item PDF at: {output_path}")

def create_bp_pdf(output_path: str):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    page.insert_text((50, 60), "VENDOR ONBOARDING FORM", fontsize=16, fontname="helv", color=(0.1, 0.4, 0.2))
    page.insert_text((50, 85), "Document Type: Business Partner Master", fontsize=11, fontname="helv")
    page.insert_text((50, 105), "-" * 60, fontsize=10, fontname="helv")
    
    fields = [
        ("Vendor Code", "V10048"),
        ("Company Name", "Apex Fasteners Global Corp"),
        ("Partner Type", "Supplier"),
        ("Telephone", "+1-800-555-0199"),
        ("Email Address", "billing@apexfasteners.com"),
        ("Street Address", "742 Evergreen Industrial Parkway"),
        ("Tax ID", "94-3829104"),
        ("Currency", "USD")
    ]
    
    y = 135
    for k, v in fields:
        page.insert_text((50, y), f"{k}:", fontsize=10, fontname="helv")
        page.insert_text((180, y), v, fontsize=10, fontname="helv")
        y += 28
        
    doc.save(output_path)
    doc.close()
    print(f"Created sample Business Partner PDF at: {output_path}")

def create_warehouse_pdf(output_path: str):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    
    page.insert_text((50, 60), "LOGISTICS FACILITY RECORD", fontsize=16, fontname="helv", color=(0.4, 0.2, 0.1))
    page.insert_text((50, 85), "Document Type: Warehouse Definition", fontsize=11, fontname="helv")
    page.insert_text((50, 105), "-" * 60, fontsize=10, fontname="helv")
    
    fields = [
        ("Warehouse Code", "WH02"),
        ("Warehouse Name", "West Coast Logistics Fulfillment Hub"),
        ("Facility Street", "1200 Pacific Marine Drive"),
        ("City", "Seattle"),
        ("Country", "US"),
        ("Inactive", "No"),
        ("Bin Locations", "No")
    ]
    
    y = 135
    for k, v in fields:
        page.insert_text((50, y), f"{k}:", fontsize=10, fontname="helv")
        page.insert_text((180, y), v, fontsize=10, fontname="helv")
        y += 28
        
    doc.save(output_path)
    doc.close()
    print(f"Created sample Warehouse PDF at: {output_path}")

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent / "uploads"
    out_dir.mkdir(parents=True, exist_ok=True)
    create_item_pdf(str(out_dir / "sample_item.pdf"))
    create_bp_pdf(str(out_dir / "sample_supplier.pdf"))
    create_warehouse_pdf(str(out_dir / "sample_warehouse.pdf"))

