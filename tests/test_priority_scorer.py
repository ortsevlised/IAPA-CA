import unittest

from src.priority_scorer import score_priority


class PriorityScorerTests(unittest.TestCase):
    def test_rule_1_expedited_override(self) -> None:
        result = score_priority(
            extracted_fields={"order_total": 30000, "order_type": "new"},
            context={"is_expedited": True, "is_month_end": False},
        )
        self.assertEqual(result.rule_id, "Rule_1")
        self.assertEqual(result.level, "CRITICAL")
        self.assertEqual(result.score, 100)

    def test_rule_2_month_end_high_value(self) -> None:
        result = score_priority(
            extracted_fields={"order_total": 12000, "order_type": "renewal"},
            context={"is_expedited": False, "is_month_end": True},
        )
        self.assertEqual(result.rule_id, "Rule_2")
        self.assertEqual(result.level, "CRITICAL")
        self.assertEqual(result.score, 95)

    def test_rule_9_default_low(self) -> None:
        result = score_priority(
            extracted_fields={"order_total": 200, "order_type": "new"},
            context={"is_expedited": False, "is_month_end": False},
        )
        self.assertEqual(result.rule_id, "Rule_9")
        self.assertEqual(result.level, "LOW")
        self.assertEqual(result.score, 20)


if __name__ == "__main__":
    unittest.main()
