import unittest
import subprocess
import json
import os

class TestHalalScreenerCLI(unittest.TestCase):
    def test_cli_helps(self):
        result = subprocess.run(
            ["python3", "dse_halal_screener/cli.py", "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("screener", result.stdout.lower() or result.stderr.lower())

    def test_cli_screener_execution(self):
        # We will mock the DSE scrape for testing or use offline database
        # Test runs CLI with sample/mock values
        result = subprocess.run(
            ["python3", "dse_halal_screener/cli.py", "--pe", "15", "--min-cf", "0", "--mock"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertGreater(len(data), 0)
        
        # Verify first item matches filters
        for item in data:
            self.assertLess(item['pe'], 15)
            self.assertGreaterEqual(item['cfo'], 0)
            self.assertNotIn(item['sector'], ["Tobacco", "Bank"])

if __name__ == "__main__":
    unittest.main()
