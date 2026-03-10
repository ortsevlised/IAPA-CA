import unittest

from src.validator import validate_extraction


class ValidatorTests(unittest.TestCase):
    def test_template_is_valid(self) -> None:
        extraction = {"extraction_path": "template"}
        result = validate_extraction(extraction)

        self.assertTrue(result.is_valid)
        self.assertFalse(result.requires_manual_fallback)
        self.assertIsNone(result.confidence)

    def test_ai_confidence_above_threshold(self) -> None:
        extraction = {"extraction_path": "ai_ocr_stub", "confidence": 0.82}
        result = validate_extraction(extraction, threshold=0.7)

        self.assertTrue(result.is_valid)
        self.assertFalse(result.requires_manual_fallback)
        self.assertEqual(result.confidence, 0.82)

    def test_ai_confidence_below_threshold(self) -> None:
        extraction = {"extraction_path": "ai_ocr_stub", "confidence": 0.61}
        result = validate_extraction(extraction, threshold=0.7)

        self.assertFalse(result.is_valid)
        self.assertTrue(result.requires_manual_fallback)
        self.assertEqual(result.confidence, 0.61)


if __name__ == "__main__":
    unittest.main()
