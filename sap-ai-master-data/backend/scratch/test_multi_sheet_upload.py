import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import httpx
from app.main import app

async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=120.0) as client:
        file_path = "uploads/fdf80a9a-8781-48b8-8c11-78b0c3b6aa31.xlsx"

        # 1. Test uploading as Item master
        print("\n=======================================================")
        print("=== 1. Testing Item Master Upload & Post ===")
        print("=======================================================")
        with open(file_path, "rb") as f:
            up_item = await client.post(
                "/api/documents/upload",
                files={"file": ("items.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"master_type": "item"}
            )
        print("Item upload status:", up_item.status_code, up_item.json().get("status"))
        wf_item_id = up_item.json().get("data", {}).get("workflow_id")
        rec_count = len(up_item.json().get("data", {}).get("extracted_records", []))
        print(f"Item records extracted: {rec_count}")
        if rec_count > 0:
            for r in up_item.json().get("data", {}).get("extracted_records", [])[:3]:
                print("  Extracted item:", r.get("ItemCode"), "|", r.get("ItemName"))
            
            # Post to SAP
            print("Posting Item Master to SAP...")
            post_res = await client.post(f"/api/master-data/{wf_item_id}/bulk-create", json={"confirmed": True})
            print("Post HTTP:", post_res.status_code)
            summary = post_res.json().get("data", {}).get("summary", {})
            print(f"Items -> Total: {summary.get('total_submitted')} | Created: {summary.get('created_count')} | Failed: {summary.get('failed_count')}")
            for r in summary.get("records", [])[:5]:
                print(f"  {r['code']} | status: {r['status']} | sap_id: {r.get('sap_object_id')} | err: {r.get('error')}")

        # 2. Test uploading as Business Partner (Vendor Master)
        print("\n=======================================================")
        print("=== 2. Testing Vendor Master Upload & Post ===")
        print("=======================================================")
        with open(file_path, "rb") as f:
            up_bp = await client.post(
                "/api/documents/upload",
                files={"file": ("vendors.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"master_type": "business_partner"}
            )
        print("BP upload status:", up_bp.status_code, up_bp.json().get("status"))
        wf_bp_id = up_bp.json().get("data", {}).get("workflow_id")
        bp_recs = up_bp.json().get("data", {}).get("extracted_records", [])
        print(f"BP records extracted: {len(bp_recs)}")
        for r in bp_recs[:3]:
            print("  Extracted BP:", r.get("CardCode"), "|", r.get("CardName"), "|", r.get("CardType"))

        if len(bp_recs) > 0:
            print("Posting BP to SAP...")
            post_bp_res = await client.post(f"/api/master-data/{wf_bp_id}/bulk-create", json={"confirmed": True})
            print("Post BP HTTP:", post_bp_res.status_code)
            summary_bp = post_bp_res.json().get("data", {}).get("summary", {})
            print(f"BPs -> Total: {summary_bp.get('total_submitted')} | Created: {summary_bp.get('created_count')} | Failed: {summary_bp.get('failed_count')}")
            for r in summary_bp.get("records", [])[:5]:
                print(f"  {r['code']} | status: {r['status']} | sap_id: {r.get('sap_object_id')} | err: {r.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
