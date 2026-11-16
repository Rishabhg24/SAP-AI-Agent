import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
import httpx
import glob
from app.main import app

async def main():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        # Find file e40335f3... (Screenshot 1 file: CUST001 ABC Pvt Ltd)
        files = glob.glob("uploads/*e40335f3*") or glob.glob("backend/uploads/*e40335f3*")
        if not files:
            print("File not found.")
            return
        f_path = files[0]
        print(f"Testing upload of: {f_path}")

        with open(f_path, "rb") as f:
            upload_res = await client.post(
                "/api/documents/upload",
                files={"file": ("customer_upload.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"master_type": "business_partner"}
            )
        
        print("Upload Status Code:", upload_res.status_code)
        up_data = upload_res.json()
        print("Upload Workflow Status:", up_data.get("status"))
        wf_id = up_data.get("data", {}).get("workflow_id")
        print("Workflow ID:", wf_id)
        assert up_data.get("status") == "READY_FOR_CONFIRMATION", f"Expected READY_FOR_CONFIRMATION, got {up_data.get('status')}"

        # Now test bulk posting to SAP
        print("\nTesting Bulk Creation in SAP via /api/master-data/{workflow_id}/bulk-create...")
        bulk_res = await client.post(
            f"/api/master-data/{wf_id}/bulk-create",
            json={"confirmed": True}
        )
        print("Bulk Post Status Code:", bulk_res.status_code)
        bulk_json = bulk_res.json()
        summary = bulk_json.get("data", {}).get("summary", {})
        print(f"Summary -> Total: {summary.get('total_submitted')} | Created: {summary.get('created_count')} | Failed: {summary.get('failed_count')}")
        for r in summary.get("records", []):
            print(f"  Record: {r['code']} | Name: {r.get('name')} | Status: {r['status']} | SAP ID: {r.get('sap_object_id')} | Error: {r.get('error')}")

        assert summary.get("failed_count") == 0, f"Expected 0 failures, got {summary.get('failed_count')}"
        print("\n>>> COMPLETE END-TO-END WORKFLOW FROM USER SCREENSHOT 1 PASSED WITH ZERO ERRORS! <<<")

if __name__ == "__main__":
    asyncio.run(main())
