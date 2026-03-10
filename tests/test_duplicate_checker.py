import unittest

from src.duplicate_checker import check_duplicate_po


class DuplicateCheckerTests(unittest.TestCase):
    def test_duplicate_on_po_and_customer(self) -> None:
        payload = {"po_number": "PO-123", "customer_id": "CUST-1"}
        existing = [{"po_number": "po-123", "customer_id": "cust-1"}]

        result = check_duplicate_po(payload, existing)

        self.assertTrue(result.is_duplicate)
        self.assertEqual(result.match_type, "po_number+customer_id")

    def test_duplicate_on_po_only(self) -> None:
        payload = {"po_number": "PO-123", "customer_id": "CUST-2"}
        existing = [{"po_number": "PO-123", "customer_id": ""}]

        result = check_duplicate_po(payload, existing)

        self.assertTrue(result.is_duplicate)
        self.assertEqual(result.match_type, "po_number")

    def test_not_duplicate(self) -> None:
        payload = {"po_number": "PO-999", "customer_id": "CUST-9"}
        existing = [{"po_number": "PO-123", "customer_id": "CUST-1"}]

        result = check_duplicate_po(payload, existing)

        self.assertFalse(result.is_duplicate)
        self.assertEqual(result.match_type, "none")


if __name__ == "__main__":
    unittest.main()
