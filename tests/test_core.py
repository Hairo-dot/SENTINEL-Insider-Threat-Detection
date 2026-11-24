import unittest
from sentinel.data import load_demo_data, normalize_activity_data
from sentinel.detection import run_detection

class SentinelCoreTests(unittest.TestCase):
    def test_demo_data_schema(self):
        df = load_demo_data(seed=3, users=4, days=5)
        for col in ["event_id", "timestamp", "user_id", "activity", "device", "resource"]:
            self.assertIn(col, df.columns)
        self.assertGreater(len(df), 10)

    def test_normalization(self):
        import pandas as pd
        raw = pd.DataFrame({"user": ["u1", "u2"], "action": ["login", "file_access"]})
        out = normalize_activity_data(raw)
        self.assertEqual(len(out), 2)
        self.assertIn("user_id", out.columns)

    def test_detection(self):
        df = load_demo_data(seed=4, users=5, days=5)
        alerts, summary = run_detection(df)
        self.assertEqual(summary["events"], len(df))
        self.assertIn("risk_score", alerts.columns)
        self.assertTrue((alerts["risk_score"] >= 0).all())
        self.assertTrue((alerts["risk_score"] <= 100).all())

if __name__ == "__main__":
    unittest.main()
