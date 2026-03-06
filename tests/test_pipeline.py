import unittest

from src.pipeline import run_classification_and_duplicate_step, run_phase1_step6


class PipelineStepTwoTests(unittest.TestCase):
    def test_halts_when_duplicate(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "po_number": "PO-123",
            "customer_id": "CUST-1",
            "existing_records": [{"po_number": "PO-123", "customer_id": "CUST-1"}],
        }

        output = run_classification_and_duplicate_step(payload)

        self.assertEqual(output["classification"]["po_format"], "pdf")
        self.assertTrue(output["duplicate_check"]["is_duplicate"])
        self.assertTrue(output["halted"])
        self.assertEqual(output["halt_reason"], "duplicate_po")

    def test_continues_when_not_duplicate(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "po_number": "PO-999",
            "customer_id": "CUST-9",
            "existing_records": [{"po_number": "PO-123", "customer_id": "CUST-1"}],
        }

        output = run_classification_and_duplicate_step(payload)

        self.assertFalse(output["duplicate_check"]["is_duplicate"])
        self.assertFalse(output["halted"])
        self.assertIsNone(output["halt_reason"])


class PipelineStepThreeTests(unittest.TestCase):
    def test_runs_template_extraction_when_not_duplicate(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "template_id": "distributor_v1",
            "po_number": "PO-1000",
            "customer_id": "CUST-77",
            "order_total": "1500.00",
            "order_type": "renewal",
            "existing_records": [{"po_number": "PO-123", "customer_id": "CUST-1"}],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertFalse(output["halted"])
        self.assertEqual(output["extraction"]["extraction_path"], "template")
        self.assertEqual(output["extraction"]["extracted_fields"]["po_number"], "PO-1000")

    def test_runs_ai_extraction_on_unknown_template(self) -> None:
        payload = {
            "filename": "po.png",
            "mime_type": "image/png",
            "source": "portal_upload",
            "template_id": "unknown_layout",
            "po_number": "PO-2000",
            "customer_id": "CUST-88",
            "ai_stub_confidence": 0.74,
            "existing_records": [],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertEqual(output["extraction"]["extraction_path"], "ai_ocr_stub")
        self.assertEqual(output["extraction"]["confidence"], 0.74)

    def test_skips_extraction_when_duplicate(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "template_id": "distributor_v1",
            "po_number": "PO-123",
            "customer_id": "CUST-1",
            "existing_records": [{"po_number": "PO-123", "customer_id": "CUST-1"}],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertTrue(output["halted"])
        self.assertIsNone(output["extraction"])


class PipelineStepFourTests(unittest.TestCase):
    def test_ai_low_confidence_routes_to_manual_fallback(self) -> None:
        payload = {
            "filename": "po.png",
            "mime_type": "image/png",
            "source": "portal_upload",
            "template_id": "unknown_layout",
            "po_number": "PO-3000",
            "customer_id": "CUST-10",
            "ai_stub_confidence": 0.62,
            "validation_threshold": 0.70,
            "existing_records": [],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertFalse(output["validation"]["is_valid"])
        self.assertTrue(output["manual_fallback"])
        self.assertTrue(output["validation"]["requires_manual_fallback"])

    def test_ai_high_confidence_passes_validation(self) -> None:
        payload = {
            "filename": "po.png",
            "mime_type": "image/png",
            "source": "portal_upload",
            "template_id": "unknown_layout",
            "po_number": "PO-3001",
            "customer_id": "CUST-11",
            "ai_stub_confidence": 0.91,
            "validation_threshold": 0.70,
            "existing_records": [],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertTrue(output["validation"]["is_valid"])
        self.assertFalse(output["manual_fallback"])

    def test_duplicate_short_circuits_validation(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "template_id": "distributor_v1",
            "po_number": "PO-123",
            "customer_id": "CUST-1",
            "existing_records": [{"po_number": "PO-123", "customer_id": "CUST-1"}],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertTrue(output["halted"])
        self.assertIsNone(output["validation"])
        self.assertFalse(output["manual_fallback"])


class PipelineStepFiveTests(unittest.TestCase):
    def test_priority_scored_when_valid(self) -> None:
        payload = {
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "template_id": "distributor_v1",
            "po_number": "PO-4000",
            "customer_id": "CUST-20",
            "order_total": "26000.00",
            "order_type": "new",
            "is_month_end": True,
            "is_expedited": False,
            "existing_records": [],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertIsNotNone(output["priority"])
        self.assertEqual(output["priority"]["level"], "CRITICAL")
        self.assertEqual(output["priority"]["rule_id"], "Rule_2")
        self.assertEqual(output["priority"]["score"], 95)
        self.assertIsNone(output["priority_skipped_reason"])

    def test_priority_skipped_for_manual_fallback(self) -> None:
        payload = {
            "filename": "po.png",
            "mime_type": "image/png",
            "source": "portal_upload",
            "template_id": "unknown_layout",
            "po_number": "PO-4001",
            "customer_id": "CUST-21",
            "ai_stub_confidence": 0.4,
            "validation_threshold": 0.7,
            "existing_records": [],
        }

        output = run_phase1_step6(payload)["payload"]

        self.assertIsNone(output["priority"])
        self.assertEqual(output["priority_skipped_reason"], "manual_fallback_required")


class PipelineStepSixTests(unittest.TestCase):
    def test_emits_downstream_json_contract(self) -> None:
        payload = {
            "triage_id": "TRIAGE-123",
            "filename": "po.pdf",
            "mime_type": "application/pdf",
            "source": "email",
            "template_id": "distributor_v1",
            "po_number": "PO-5000",
            "customer_id": "CUST-50",
            "region": "APAC",
            "order_total": "12000.00",
            "order_type": "new",
            "is_expedited": False,
            "is_month_end": False,
            "existing_records": [],
        }

        output = run_phase1_step6(payload)

        self.assertEqual(output["schema_version"], "1.0.0")
        self.assertEqual(output["triage_id"], "TRIAGE-123")
        self.assertEqual(output["disposition"], "READY_FOR_ORDER_FULFILLMENT")
        self.assertEqual(output["region"], "APAC")
        self.assertEqual(output["route"], "APAC")
        self.assertIn("payload", output)


if __name__ == "__main__":
    unittest.main()
