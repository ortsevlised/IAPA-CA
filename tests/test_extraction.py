import unittest

from src.ai_extractor import extract_with_ai_ocr_stub
from src.template_extractor import extract_with_template, should_use_template_path


class ExtractionTests(unittest.TestCase):
    def test_uses_template_path_for_known_template(self) -> None:
        payload = {
            "template_id": "distributor_v1",
            "po_number": "PO-1",
            "customer_id": "CUST-1",
            "order_total": "1200.00",
            "order_type": "renewal",
        }

        self.assertTrue(should_use_template_path(payload))
        result = extract_with_template(payload)

        self.assertEqual(result.extraction_path, "template")
        self.assertEqual(result.template_id, "distributor_v1")
        self.assertEqual(result.extracted_fields["order_type"], "renewal")
        self.assertEqual(result.extracted_fields["order_total"], 1200.0)

    def test_ai_stub_includes_confidence(self) -> None:
        payload = {
            "template_id": "unknown_layout",
            "ai_stub_confidence": 0.81,
            "ai_stub_result": {
                "po_number": "PO-9",
                "customer_id": "CUST-9",
                "order_total": 9999.0,
                "order_type": "new",
                "currency": "USD",
            },
        }

        result = extract_with_ai_ocr_stub(payload)
        self.assertEqual(result.extraction_path, "ai_ocr_stub")
        self.assertEqual(result.confidence, 0.81)
        self.assertEqual(result.extracted_fields["po_number"], "PO-9")


if __name__ == "__main__":
    unittest.main()
