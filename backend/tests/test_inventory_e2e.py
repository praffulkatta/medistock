import json
import os
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.auth import Pharmacy, User
from app.models.catalog import Category, Medicine
from app.models.inventory import Location, MedicineBatch, Stock, Supplier
from app.models.notifications import Notification
from app.models.transactions import Purchase, PurchaseItem, Sale, SaleItem, StockTransaction


BASE_URL = os.getenv("MEDISTOCK_TEST_URL", "http://127.0.0.1:8000") + "/api/v1"


def api_request(method, path, payload=None):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        BASE_URL + path,
        data=body,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as response:
        raw = response.read()
        return response.code, json.loads(raw) if raw else None


class InventoryEndToEndTests(unittest.TestCase):
    pharmacy_id = None

    def call(self, method, path, expected, payload=None):
        status_code, response = api_request(method, path, payload)
        self.assertEqual(status_code, expected, (method, path, response))
        return response

    def test_purchase_transfer_fefo_search_and_audit(self):
        pharmacy = self.call("POST", "/pharmacies/", 201, {"name": "MediStock automated test"})
        self.pharmacy_id = pharmacy["id"]
        pharmacy_id = self.pharmacy_id

        category = self.call("POST", "/categories/", 201, {"name": "Analgesics", "pharmacy_id": pharmacy_id})
        self.call("POST", "/categories/", 409, {"name": "analgesics", "pharmacy_id": pharmacy_id})
        self.call("POST", "/categories/", 404, {"name": "Missing pharmacy", "pharmacy_id": "00000000-0000-0000-0000-000000000001"})
        supplier = self.call("POST", "/suppliers/", 201, {"name": "Test supplier", "pharmacy_id": pharmacy_id})
        self.call("PUT", f"/suppliers/{supplier['id']}", 200, {"contact_info": "test@example.invalid"})
        supplier = self.call("GET", f"/suppliers/{supplier['id']}", 200)

        def create_location(name, location_type, level, parent_id=None):
            data = {"name": name, "type": location_type, "level": level, "pharmacy_id": pharmacy_id}
            if parent_id:
                data["parent_id"] = parent_id
            return self.call("POST", "/locations/", 201, data)

        block_a = create_location("Block A", "Block", 1)
        self.call("POST", "/locations/", 400, {"name": "Invalid root", "type": "Rack", "level": 2, "pharmacy_id": pharmacy_id})
        rack_a = create_location("Rack 03", "Rack", 2, block_a["id"])
        shelf_a = create_location("Shelf 02", "Shelf", 3, rack_a["id"])
        bin_a = create_location("Bin 04", "Bin", 4, shelf_a["id"])
        block_b = create_location("Block B", "Block", 1)
        rack_b = create_location("Rack 01", "Rack", 2, block_b["id"])
        shelf_b = create_location("Shelf 01", "Shelf", 3, rack_b["id"])
        bin_b = create_location("Bin 02", "Bin", 4, shelf_b["id"])

        medicine = self.call("POST", "/medicines/", 201, {
            "name": "Dolo 650",
            "generic_name": "Paracetamol",
            "manufacturer": "Micro Labs",
            "strength": "650 mg",
            "category_id": category["id"],
            "pharmacy_id": pharmacy_id,
            "min_stock_level": 10,
        })
        self.call("POST", "/medicines/", 404, {
            "name": "Invalid category medicine", "generic_name": "Test", "category_id": "00000000-0000-0000-0000-000000000001",
            "pharmacy_id": pharmacy_id,
        })
        self.call("PUT", f"/categories/{category['id']}", 200, {"name": "Pain relief"})
        expiry_a = (date.today() + timedelta(days=7)).isoformat()
        expiry_b = (date.today() + timedelta(days=120)).isoformat()
        expiry_old = (date.today() - timedelta(days=1)).isoformat()

        initial = self.call("POST", "/purchases", 201, {
            "pharmacy_id": pharmacy_id,
            "supplier_id": supplier["id"],
            "invoice_number": "TEST-001",
            "items": [
                {"medicine_id": medicine["id"], "batch_number": "DL1024", "expiry_date": expiry_a,
                 "cost_price": 5, "selling_price": 10, "quantity": 20, "location_id": bin_a["id"]},
                {"medicine_id": medicine["id"], "batch_number": "DL2045", "expiry_date": expiry_b,
                 "cost_price": 6, "selling_price": 11, "quantity": 50, "location_id": bin_b["id"]},
            ],
        })
        batch_a, batch_b = initial["items"]
        self.call("POST", "/purchases", 404, {
            "pharmacy_id": pharmacy_id, "supplier_id": "00000000-0000-0000-0000-000000000001",
            "items": [{"medicine_id": medicine["id"], "batch_number": "MISSING-SUPPLIER", "expiry_date": expiry_b,
                       "cost_price": 1, "selling_price": 1, "quantity": 1, "location_id": bin_a["id"]}],
        })
        self.call("POST", "/purchases", 422, {
            "pharmacy_id": pharmacy_id, "supplier_id": supplier["id"],
            "items": [{"medicine_id": medicine["id"], "batch_number": "ZERO", "expiry_date": expiry_b,
                       "cost_price": 1, "selling_price": 1, "quantity": 0, "location_id": bin_a["id"]}],
        })
        self.call("POST", "/purchases", 400, {
            "pharmacy_id": pharmacy_id, "supplier_id": supplier["id"],
            "items": [{"medicine_id": medicine["id"], "batch_number": "OLD", "expiry_date": expiry_old,
                       "cost_price": 1, "selling_price": 1, "quantity": 1, "location_id": bin_a["id"]}],
        })

        # Seed legacy expired stock to verify the system flags it and FEFO excludes it.
        expired_batch = self.call("POST", "/batches", 201, {
            "medicine_id": medicine["id"], "supplier_id": supplier["id"],
            "batch_number": "DL-EXPIRED", "expiry_date": expiry_old,
            "cost_price": 4, "selling_price": 8,
        })
        with SessionLocal() as db:
            db.add(Stock(batch_id=expired_batch["id"], location_id=bin_a["id"], quantity=Decimal("3")))
            db.add(StockTransaction(batch_id=expired_batch["id"], location_id=bin_a["id"], change_qty=3, reason="ADJUSTMENT"))
            db.commit()

        search = self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=dOlO", 200)
        self.assertEqual(search["total"], 1)
        self.assertEqual(float(search["results"][0]["total_quantity"]), 73)
        result = search["results"][0]
        self.assertEqual(result["batches"][0]["expiry_status"], "EXPIRED")
        self.assertEqual(result["batches"][1]["expiry_status"], "EXPIRING_SOON")
        self.assertEqual(result["batches"][2]["expiry_status"], "SAFE")
        self.assertEqual(result["batches"][1]["locations"][0]["location_path"], ["Block A", "Rack 03", "Shelf 02", "Bin 04"])
        self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=DL1024", 200)
        self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=micro", 200)

        self.call("POST", "/stock/transfers", 400, {
            "pharmacy_id": pharmacy_id,
            "batch_id": batch_b["batch_id"],
            "source_location_id": bin_b["id"],
            "destination_location_id": bin_a["id"],
            "quantity": 999,
        })
        self.call("POST", "/stock/transfers", 200, {
            "pharmacy_id": pharmacy_id,
            "batch_id": batch_b["batch_id"],
            "source_location_id": bin_b["id"],
            "destination_location_id": bin_a["id"],
            "quantity": 20,
        })
        after_transfer = self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=Dolo", 200)
        self.assertEqual(float(after_transfer["results"][0]["total_quantity"]), 73)
        stock_rows = self.call("GET", f"/stock?pharmacy_id={pharmacy_id}", 200)
        batch_b_rows = [row for row in stock_rows if row["batch_id"] == batch_b["batch_id"]]
        self.assertEqual(sum(float(row["quantity"]) for row in batch_b_rows), 50)

        self.call("POST", "/purchases", 201, {
            "pharmacy_id": pharmacy_id, "supplier_id": supplier["id"],
            "items": [{"medicine_id": medicine["id"], "batch_number": "DL2045", "expiry_date": expiry_b,
                       "cost_price": 6, "selling_price": 11, "quantity": 5, "location_id": bin_b["id"]}],
        })
        self.call("POST", "/purchases", 409, {
            "pharmacy_id": pharmacy_id, "supplier_id": supplier["id"],
            "items": [{"medicine_id": medicine["id"], "batch_number": "DL2045", "expiry_date": expiry_a,
                       "cost_price": 6, "selling_price": 11, "quantity": 5, "location_id": bin_b["id"]}],
        })

        unchanged = self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=Dolo", 200)["results"][0]["total_quantity"]
        self.call("POST", "/sales/", 422, {"pharmacy_id": pharmacy_id, "items": [{"medicine_id": medicine["id"], "quantity": 0, "unit_price": 10}]})
        self.call("POST", "/sales/", 404, {"pharmacy_id": pharmacy_id, "items": [{"medicine_id": "00000000-0000-0000-0000-000000000001", "quantity": 1, "unit_price": 10}]})
        self.call("POST", "/sales/", 400, {"pharmacy_id": pharmacy_id, "items": [{"medicine_id": medicine["id"], "quantity": 999, "unit_price": 10}]})
        self.call("GET", "/sales/00000000-0000-0000-0000-000000000001", 404)
        after_failed_sale = self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=Dolo", 200)["results"][0]["total_quantity"]
        self.assertEqual(float(after_failed_sale), float(unchanged))

        sale_one = self.call("POST", "/sales/", 201, {"pharmacy_id": pharmacy_id, "items": [{"medicine_id": medicine["id"], "quantity": 10, "unit_price": 10}]})
        sale_two = self.call("POST", "/sales/", 201, {"pharmacy_id": pharmacy_id, "items": [{"medicine_id": medicine["id"], "quantity": 15, "unit_price": 10}]})
        self.assertTrue(all(item["batch_id"] != expired_batch["id"] for item in sale_one["items"] + sale_two["items"]))
        self.assertTrue(any(item["batch_id"] == batch_a["batch_id"] for item in sale_one["items"]))
        self.assertTrue(any(item["batch_id"] == batch_a["batch_id"] for item in sale_two["items"]))

        final_search = self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=DL1024", 200)
        batches = {batch["batch_number"]: batch for batch in final_search["results"][0]["batches"]}
        self.assertEqual(float(final_search["results"][0]["total_quantity"]), 53)
        self.assertEqual(float(batches["DL1024"]["quantity"]), 0)
        self.assertEqual(float(batches["DL2045"]["quantity"]), 50)
        self.assertEqual(float(batches["DL-EXPIRED"]["quantity"]), 3)

        self.call("PUT", f"/medicines/{medicine['id']}", 200, {"min_stock_level": 60})
        dashboard = self.call("GET", f"/dashboard/{pharmacy_id}", 200)
        self.assertEqual(dashboard["medicine_count"], 1)
        self.assertEqual(dashboard["low_stock_count"], 1)
        self.assertEqual(float(dashboard["expired_quantity"]), 3)
        movements = self.call("GET", f"/transactions?pharmacy_id={pharmacy_id}", 200)
        self.assertGreaterEqual(len(movements), 9)
        purchases = self.call("GET", f"/purchases?pharmacy_id={pharmacy_id}", 200)
        self.assertEqual(len(purchases), 2)

        # A two-line receipt with an invalid second line must roll back its valid first line.
        self.call("POST", "/purchases", 404, {
            "pharmacy_id": pharmacy_id, "supplier_id": supplier["id"],
            "items": [
                {"medicine_id": medicine["id"], "batch_number": "ROLLBACK-1", "expiry_date": expiry_b,
                 "cost_price": 1, "selling_price": 2, "quantity": 9, "location_id": bin_b["id"]},
                {"medicine_id": medicine["id"], "batch_number": "ROLLBACK-2", "expiry_date": expiry_b,
                 "cost_price": 1, "selling_price": 2, "quantity": 9, "location_id": "00000000-0000-0000-0000-000000000001"},
            ],
        })
        rollback_check = self.call("GET", f"/medicines/search?pharmacy_id={pharmacy_id}&q=ROLLBACK-1", 200)
        self.assertEqual(rollback_check["total"], 0)

    def tearDown(self):
        if not self.pharmacy_id:
            return
        pharmacy_id = self.pharmacy_id
        db = SessionLocal()
        try:
            medicine_ids = select(Medicine.id).where(Medicine.pharmacy_id == pharmacy_id)
            batch_ids = select(MedicineBatch.id).where(MedicineBatch.medicine_id.in_(medicine_ids))
            sale_ids = select(Sale.id).where(Sale.pharmacy_id == pharmacy_id)
            purchase_ids = select(Purchase.id).where(Purchase.pharmacy_id == pharmacy_id)
            db.query(StockTransaction).filter(StockTransaction.batch_id.in_(batch_ids)).delete(synchronize_session=False)
            db.query(SaleItem).filter(SaleItem.sale_id.in_(sale_ids)).delete(synchronize_session=False)
            db.query(PurchaseItem).filter(PurchaseItem.purchase_id.in_(purchase_ids)).delete(synchronize_session=False)
            db.query(Stock).filter(Stock.batch_id.in_(batch_ids)).delete(synchronize_session=False)
            db.query(Sale).filter(Sale.id.in_(sale_ids)).delete(synchronize_session=False)
            db.query(Purchase).filter(Purchase.id.in_(purchase_ids)).delete(synchronize_session=False)
            db.query(MedicineBatch).filter(MedicineBatch.medicine_id.in_(medicine_ids)).delete(synchronize_session=False)
            db.query(Notification).filter(Notification.pharmacy_id == pharmacy_id).delete(synchronize_session=False)
            db.query(User).filter(User.pharmacy_id == pharmacy_id).delete(synchronize_session=False)
            db.query(Medicine).filter(Medicine.pharmacy_id == pharmacy_id).delete(synchronize_session=False)
            db.query(Category).filter(Category.pharmacy_id == pharmacy_id).delete(synchronize_session=False)
            db.query(Supplier).filter(Supplier.pharmacy_id == pharmacy_id).delete(synchronize_session=False)
            for level in (4, 3, 2, 1):
                db.query(Location).filter(
                    Location.pharmacy_id == pharmacy_id, Location.level == level
                ).delete(synchronize_session=False)
            db.query(Pharmacy).filter(Pharmacy.id == pharmacy_id).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
