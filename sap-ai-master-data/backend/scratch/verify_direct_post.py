import urllib.request
import json
import time

def test_create(name, payload):
    print(f"\n=== Testing: {name} ===")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/master-data/bulk-create-direct",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req) as res:
            resp = json.loads(res.read().decode("utf-8"))
            summary = resp["data"]["summary"]
            print(f"Elapsed: {time.time()-t0:.2f}s | Status: {resp['status']} | Created: {summary['created_count']} | Failed: {summary['failed_count']}")
            for r in summary["records"]:
                print(f"  Result -> Code: {r['code']} | Status: {r['status']} | SAP ID: {r.get('sap_object_id')} | Error: {r.get('error')}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print("General Error:", e)

if __name__ == "__main__":
    t_now = int(time.time())

    # 1. Item Master: only ItemCode & ItemName
    test_create("Item Master (Only ItemCode & ItemName)", {
        "master_type": "item",
        "confirmed": True,
        "skip_duplicates": False,
        "records": [
            {"ItemCode": f"ITM{t_now % 100000}", "ItemName": "High Tensile Steel Bolt M12"}
        ]
    })

    # 2. Business Partner: messy columns & invalid email header (exact issue from user screenshot)
    test_create("Business Partner (Messy columns & invalid email)", {
        "master_type": "business_partner",
        "confirmed": True,
        "skip_duplicates": False,
        "records": [
            {
                "CardCode": f"CUST{t_now % 100000}",
                "CardName": "MG Creative Automation Corp",
                "CardType": "cSupplier",
                "EmailAddress": "Contact Person Name | P.A.N. No",
                "AddressLine2": "Invalid Extra Property AddressLine2",
                "FirstName": "Invalid Extra Property FirstName",
                "ItemsGroupCode": "100"
            }
        ]
    })

    # 3. Warehouse: only WarehouseCode
    test_create("Warehouse Master (Only WarehouseCode)", {
        "master_type": "warehouse",
        "confirmed": True,
        "skip_duplicates": False,
        "records": [
            {"WarehouseCode": f"W{t_now % 10000}"}
        ]
    })
