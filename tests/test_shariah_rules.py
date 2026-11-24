"""Regression tests for the Shariah screening rules (AAOIFI Shariah Standard No. 21)."""
import pathlib

import yaml
from bs4 import BeautifulSoup

from dse_halal_screener.screener import Stock, _debt_ratio, filter_halal


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
