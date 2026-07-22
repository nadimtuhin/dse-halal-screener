import unittest
from dse_halal_screener.screener import Stock, filter_halal

class TestHalalIntegration(unittest.TestCase):
    def test_halal_integration(self):
        stocks = [
            Stock(symbol="GP", sector="Telecommunication", debt_ratio=0.1, pe=12.29, cfo=5.0, eps=12.29, nav=25.28),
            Stock(symbol="BATBC", sector="Tobacco", debt_ratio=0.05, pe=9.5, cfo=8.0, eps=9.5, nav=10.0),
        ]
        results = filter_halal(stocks, min_cfo=0)
        symbols = [s.symbol for s in results]
        self.assertIn("GP", symbols)
        self.assertNotIn("BATBC", symbols)

if __name__ == '__main__':
    unittest.main()
