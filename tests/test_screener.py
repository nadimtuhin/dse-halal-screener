import unittest
from dse_halal_screener.screener import filter_halal, Stock

class TestHalalScreener(unittest.TestCase):
    def test_filter_halal_removes_tobacco_and_banking(self):
        stocks = [
            Stock(symbol="GP", sector="Telecommunication", debt_ratio=0.1, pe=12.29, cfo=5000),
            Stock(symbol="BATBC", sector="Tobacco", debt_ratio=0.05, pe=9.5, cfo=8000),
            Stock(symbol="EBL", sector="Bank", debt_ratio=0.8, pe=6.2, cfo=1000),
        ]
        halal_stocks = filter_halal(stocks)
        symbols = [s.symbol for s in halal_stocks]
        self.assertIn("GP", symbols)
        self.assertNotIn("BATBC", symbols)
        self.assertNotIn("EBL", symbols)

    def test_filter_halal_removes_high_debt(self):
        stocks = [
            Stock(symbol="GP", sector="Telecommunication", debt_ratio=0.1, pe=12.29, cfo=5000),
            Stock(symbol="DEBTCO", sector="Telecommunication", debt_ratio=0.45, pe=10.0, cfo=2000),
        ]
        halal_stocks = filter_halal(stocks)
        symbols = [s.symbol for s in halal_stocks]
        self.assertIn("GP", symbols)
        self.assertNotIn("DEBTCO", symbols)

    def test_filter_halal_favors_operating_cashflow(self):
        stocks = [
            Stock(symbol="GP", sector="Telecommunication", debt_ratio=0.1, pe=12.29, cfo=5000),
            Stock(symbol="LOWCF", sector="Telecommunication", debt_ratio=0.1, pe=12.29, cfo=-100),
        ]
        halal_stocks = filter_halal(stocks, min_cfo=0)
        symbols = [s.symbol for s in halal_stocks]
        self.assertIn("GP", symbols)
        self.assertNotIn("LOWCF", symbols)
        
if __name__ == "__main__":
    unittest.main()
