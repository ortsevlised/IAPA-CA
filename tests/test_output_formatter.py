import unittest

from src.output_formatter import emit_downstream_json


class OutputFormatterTests(unittest.TestCase):
    def test_ready_for_order_fulfillment_contract(self) -> None:
        step5 = {
            "halted": False,
            "manual_fallback": False,
            "priority": {"score": 85, "level": "HIGH", "rule_id": "Rule_3"},
        }
        payload = {"po_number": "PO-1", "region": "EMEA"}

        output = emit_downstream_json(step5, payload, generated_at="2026-03-06T00:00:00Z")

        self.assertEqual(output["schema_version"], "1.0.0")
        self.assertEqual(output["triage_id"], "PO-1")
        self.assertEqual(output["disposition"], "READY_FOR_ORDER_FULFILLMENT")
        self.assertEqual(output["region"], "EMEA")
        self.assertEqual(output["route"], "EMEA")
        self.assertIsNone(output["reason"])

    def test_manual_review_contract(self) -> None:
        step5 = {"halted": False, "manual_fallback": True, "priority": None}
        payload = {"po_number": "PO-2", "region": "APAC"}

        output = emit_downstream_json(step5, payload, generated_at="2026-03-06T00:00:00Z")

        self.assertEqual(output["disposition"], "MANUAL_REVIEW")
        self.assertEqual(output["region"], "APAC")
        self.assertEqual(output["route"], "manual_queue_APAC")
        self.assertEqual(output["reason"], "low_extraction_confidence")

    def test_duplicate_contract(self) -> None:
        step5 = {"halted": True, "halt_reason": "duplicate_po", "manual_fallback": False, "priority": None}
        payload = {"po_number": "PO-3"}

        output = emit_downstream_json(step5, payload, generated_at="2026-03-06T00:00:00Z")

        self.assertEqual(output["disposition"], "REJECT_DUPLICATE")
        self.assertEqual(output["route"], "stop")
        self.assertEqual(output["reason"], "duplicate_po")

    def test_defaults_region_to_usa(self) -> None:
        step5 = {"halted": False, "manual_fallback": False, "priority": {"score": 20, "level": "LOW", "rule_id": "Rule_9"}}
        payload = {"po_number": "PO-4"}

        output = emit_downstream_json(step5, payload, generated_at="2026-03-06T00:00:00Z")
        self.assertEqual(output["region"], "USA")
        self.assertEqual(output["route"], "USA")


if __name__ == "__main__":
    unittest.main()
