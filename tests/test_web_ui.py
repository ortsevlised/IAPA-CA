import unittest

from src.web_ui import process_payload


class WebUiTests(unittest.TestCase):
    def test_process_payload_returns_contract(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "template_id": "distributor_v1",
            "po_number": "PO-9000",
            "customer_id": "CUST-90",
            "region": "EMEA",
            "order_total": "11000.00",
            "order_type": "new",
            "is_month_end": False,
            "is_expedited": False,
            "existing_records": [],
        }

        output = process_payload(payload)

        self.assertEqual(output["schema_version"], "1.0.0")
        self.assertEqual(output["disposition"], "READY_FOR_ORDER_FULFILLMENT")
        self.assertEqual(output["route"], "EMEA")
        self.assertIn("payload", output)

    def test_process_payload_accepts_document_block(self) -> None:
        payload = {
            "source": "portal_upload",
            "template_id": "unknown_layout",
            "is_month_end": False,
            "is_expedited": False,
            "existing_records": [],
            "document": {
                "filename": "mail.eml",
                "mime_type": "message/rfc822",
                "text": "PO-777 CUST-77 USD 1200 renewal",
            },
        }

        output = process_payload(payload)

        self.assertEqual(output["schema_version"], "1.0.0")
        self.assertIn("classification", output["payload"])
        self.assertEqual(output["payload"]["input"]["filename"], "mail.eml")

    def test_process_payload_infers_defaults_and_lowconf(self) -> None:
        payload = {
            "document": {
                "filename": "03_unknown_lowconf.txt",
                "mime_type": "text/plain",
                "text": "PO-3000 CUST-30 USD 8000 new",
            },
        }

        output = process_payload(payload)

        self.assertEqual(output["payload"]["input"]["source"], "portal_upload")
        self.assertEqual(output["payload"]["extraction"]["extraction_path"], "ai_ocr_stub")
        self.assertTrue(output["payload"]["manual_fallback"])

    def test_process_payload_detects_duplicate_from_document_text(self) -> None:
        payload = {
            "document": {
                "filename": "02_duplicate_po.txt",
                "mime_type": "text/plain",
                "text": "PO-123 CUST-1 USD 1200 renewal",
            }
        }

        output = process_payload(payload)

        self.assertEqual(output["disposition"], "REJECT_DUPLICATE")
        self.assertEqual(output["reason"], "duplicate_po")

    def test_process_payload_infers_region_from_text(self) -> None:
        payload = {
            "document": {
                "filename": "apac_order.txt",
                "mime_type": "text/plain",
                "text": "PO-991 CUST-99 APAC customer order",
            }
        }

        output = process_payload(payload)
        self.assertEqual(output["region"], "APAC")
        self.assertEqual(output["route"], "APAC")


if __name__ == "__main__":
    unittest.main()
