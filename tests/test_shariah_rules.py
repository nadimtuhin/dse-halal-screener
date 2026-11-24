"""Regression tests for the Shariah screening rules (AAOIFI Shariah Standard No. 21)."""
import pathlib

import yaml
from bs4 import BeautifulSoup

from dse_halal_screener import screener
from dse_halal_screener.screener import MAX_DEBT_TO_MARKET_CAP, Stock, _debt_ratio, filter_halal


def _soup(body):
    return BeautifulSoup(f"<html><body>{body}</body></html>", "html.parser")


LOANS = "<table><tr><td>Short-term loan (mn)</td><td>{st}</td></tr>" \
        "<tr><td>Long-term loan (mn)</td><td>{lt}</td></tr></table>"


# --- AAOIFI debt threshold is 30% of market cap, not 33% ---------------------

def test_debt_ratio_above_aaoifi_30_percent_is_rejected():
    stocks = [Stock(symbol="LEV31", sector="Cement", debt_ratio=0.31)]
    assert filter_halal(stocks) == []


def test_debt_ratio_exactly_30_percent_passes():
    # AAOIFI: interest-bearing debt must "not exceed" 30% of market value.
    stocks = [Stock(symbol="LEV30", sector="Cement", debt_ratio=0.30)]
    assert [s.symbol for s in filter_halal(stocks)] == ["LEV30"]


# --- unknown data must not be treated as zero debt (a pass) ------------------

def test_unknown_market_cap_is_not_zero_debt():
    soup = _soup(LOANS.format(st="500.0", lt="500.0"))
    assert _debt_ratio(soup, price=0.0, shares=0.0) is None


def test_missing_loan_rows_is_not_zero_debt():
    # e.g. DSE changes its page layout and the loan rows disappear.
    soup = _soup("<p>no loan data here</p>")
    assert _debt_ratio(soup, price=100.0, shares=1_000_000) is None


def test_reported_zero_loans_is_zero_debt():
    soup = _soup(LOANS.format(st="-", lt="0.00"))
    assert _debt_ratio(soup, price=100.0, shares=1_000_000) == 0.0


def test_known_debt_ratio_is_computed():
    # 25mn debt / (100 * 1mn shares = 100mn market cap) = 0.25
    soup = _soup(LOANS.format(st="10.0", lt="15.0"))
    assert _debt_ratio(soup, price=100.0, shares=1_000_000) == 0.25


def test_filter_halal_rejects_unknown_debt_ratio():
    stocks = [Stock(symbol="NODATA", sector="Cement", debt_ratio=None)]
    assert filter_halal(stocks) == []


# --- conventional insurance is a non-permissible core business ---------------

def test_conventional_insurance_sector_is_excluded():
    stocks = [Stock(symbol="GREENDELT", sector="Insurance", debt_ratio=0.0)]
    assert filter_halal(stocks) == []


# --- CI must not swallow lint failures ---------------------------------------

def test_ci_lint_step_does_not_ignore_failures():
    ci = yaml.safe_load(
        (pathlib.Path(__file__).parent.parent / ".github/workflows/ci.yml").read_text()
    )
    for job in ci["jobs"].values():
        for step in job["steps"]:
            run = step.get("run", "")
            assert "|| true" not in run, f"step {step.get('name')!r} hides failures"


# --- the 30% limit is applied to the exact ratio, not a rounded one ----------

COMPANY_PAGE = (
    "<table><tr><td>Sector</td><td>Cement</td></tr>"
    "<tr><td>Closing Price</td><td>100.0</td></tr>"
    "<tr><td>Total No. of Outstanding Securities</td><td>1,000,000</td></tr>"
    "<tr><td>Current P/E Ratio using Basic EPS</td><td>10.0</td></tr>"
    "<tr><td>Short-term loan (mn)</td><td>{st}</td></tr>"
    "<tr><td>Long-term loan (mn)</td><td>0.0</td></tr></table>"
)


def test_debt_ratio_just_above_30_percent_is_not_rounded_into_a_pass(monkeypatch):
    # 30.04mn debt / 100mn market cap = 30.04%, which exceeds the AAOIFI 30% limit
    # but rounds to 0.300 at three decimals.
    monkeypatch.setattr(screener, "_fetch_html",
                        lambda url: f"<html><body>{COMPANY_PAGE.format(st='30.04')}</body></html>")
    stock = screener.get_stock_data("LEV3004")
    assert stock is not None
    assert stock.debt_ratio > MAX_DEBT_TO_MARKET_CAP
    assert filter_halal([stock]) == []
