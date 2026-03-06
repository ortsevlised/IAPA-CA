import unittest

from src.classifier import classify_po_format_and_source


class ClassifierTests(unittest.TestCase):
    def test_pdf_email_attachment(self) -> None:
        payload = {
            "filename": "po_1001.pdf",
            "mime_type": "application/pdf",
            "source": "email",
        }

        result = classify_po_format_and_source(payload)

        self.assertEqual(result.po_format, "pdf")
        self.assertEqual(result.source, "email_attachment")

    def test_portal_text_upload(self) -> None:
        payload = {
            "filename": "order.txt",
            "mime_type": "text/plain",
            "channel": "portal_upload",
        }

        result = classify_po_format_and_source(payload)

        self.assertEqual(result.po_format, "text")
        self.assertEqual(result.source, "portal_upload")

    def test_unknown_when_no_signals(self) -> None:
        result = classify_po_format_and_source({})
        self.assertEqual(result.po_format, "unknown")
        self.assertEqual(result.source, "unknown")


if __name__ == "__main__":
    unittest.main()
