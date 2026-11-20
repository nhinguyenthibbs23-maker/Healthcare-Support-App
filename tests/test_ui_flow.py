"""UI-flow, AI Assistant and Exact Shapley tests for GlucoGuide.
Run: python -m unittest discover -s tests -v
"""

import json
import unittest
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

M = json.loads((ROOT / "models" / "model_meta.json").read_text())

HIGH = dict(Age=10, BMI=38.0, HighBP=1, HighChol=1, GenHlth=4,
            Smoker=1, PhysActivity=0, DiffWalk=1)
LOW = dict(Age=2, BMI=22.0, HighBP=0, HighChol=0, GenHlth=1,
           Smoker=0, PhysActivity=1, DiffWalk=0)


class ExplanationTests(unittest.TestCase):

    def test_contributions_add_up_to_estimate(self):
        from utils.explanation import shapley
        from utils.prediction import load_pipeline

        pipe = load_pipeline()
        examples = (
            HIGH, LOW,
            dict(Age=9, BMI=98.0, HighBP=1, HighChol=0, GenHlth=3,
                 Smoker=0, PhysActivity=1, DiffWalk=1),
        )

        for answers in examples:
            phi, base, total = shapley(pipe, answers, M)
            probability = pipe.predict_proba(
                pd.DataFrame([answers], columns=M["features"])
            )[0, 1]
            # Exact Shapley values must sum to probability - base
            self.assertAlmostEqual(sum(phi.values()), probability - base, places=6)
            self.assertAlmostEqual(total, probability, places=6)

    def test_extreme_bmi_prediction_is_valid(self):
        from utils.prediction import predict

        for bmi in (15.0, 25.0, 40.0, 60.0, 98.0):
            probability = predict({**HIGH, "BMI": bmi})
            self.assertTrue(
                0.0 <= probability <= 1.0,
                f"Invalid probability for BMI={bmi}: {probability}",
            )

    def test_explain_returns_all_features(self):
        from utils.explanation import explain
        from utils.prediction import load_pipeline

        pipe = load_pipeline()
        df, desc = explain(pipe, HIGH, M)
        self.assertEqual(len(df), 8)
        self.assertTrue("Exact Shapley" in desc)


class AIAssistantTests(unittest.TestCase):

    def test_offline_explanation_generation(self):
        from utils.ai_service import get_offline_explanation, build_system_instruction

        context = {
            "probability": 0.285,
            "threshold": 0.1693,
            "is_elevated": True,
            "answers": HIGH,
            "top_factors": [
                {"Factor": "High Blood Pressure", "Feature": "HighBP", "Contribution": 0.08, "Direction": "Raises score"},
                {"Factor": "Age Group", "Feature": "Age", "Contribution": 0.05, "Direction": "Raises score"}
            ]
        }

        # Test question about result explanation
        res_text = get_offline_explanation("Giải thích kết quả của tôi", context)
        self.assertIn("28.5%", res_text)
        self.assertIn("16.9%", res_text)

        # Test question about factors
        factor_text = get_offline_explanation("Yếu tố nào ảnh hưởng?", context)
        self.assertIn("Exact Shapley", factor_text)

        # Test system instruction builder
        sys_prompt = build_system_instruction(context)
        self.assertIn("GlucoGuide AI Assistant", sys_prompt)
        self.assertIn("CDC BRFSS 2015", sys_prompt)


class ModelIntegrityTests(unittest.TestCase):

    def test_verified_test_metrics(self):
        test_m = M["test_metrics"]
        self.assertAlmostEqual(test_m["roc_auc"], 0.819466, places=4)
        self.assertAlmostEqual(test_m["average_precision"], 0.4175, places=3)
        self.assertAlmostEqual(test_m["brier"], 0.0981, places=3)
        self.assertEqual(test_m["n"], 50886)
        self.assertEqual(test_m["positive_count"], 7064)

        cm = test_m["confusion_matrix"]
        self.assertEqual(cm[0][0], 33539)  # TN
        self.assertEqual(cm[0][1], 10283)  # FP
        self.assertEqual(cm[1][0], 2054)   # FN
        self.assertEqual(cm[1][1], 5010)   # TP

    def test_model_feature_count(self):
        features = M["features"]
        self.assertEqual(len(features), 8)
        expected = ["Age", "BMI", "HighBP", "HighChol", "GenHlth", "Smoker", "PhysActivity", "DiffWalk"]
        self.assertEqual(features, expected)


if __name__ == "__main__":
    unittest.main()
