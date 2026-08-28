import requests
import urllib3
from bs4 import BeautifulSoup
import re
import os
import time
import hashlib
import tempfile

# dsebd.org has a broken TLS cert chain, so we skip verification; silence the noisy warning.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_CACHE_DIR = os.path.join(tempfile.gettempdir(), "dse_screener_cache")
_CACHE_TTL = 60  # seconds

def _fetch_html(url):
    """GET url, caching the raw HTML on disk for _CACHE_TTL seconds.

    A stock's page barely changes minute-to-minute, so re-running the screener
    (or fetching the same symbol twice) shouldn't hammer dsebd.org.
    """
    os.makedirs(_CACHE_DIR, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()
    path = os.path.join(_CACHE_DIR, key)

    if os.path.exists(path) and time.time() - os.path.getmtime(path) < _CACHE_TTL:
        with open(path, encoding="utf-8") as f:
            return f.read()

    r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, verify=False, timeout=15)
    # Only cache a fully-loaded company page. A truncated/error response (e.g. a slow
    # fetch that timed out mid-body) would otherwise be served stale for the whole TTL.
    if r.status_code == 200 and "Total No. of Outstanding Securities" in r.text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
    return r.text

class Stock:
    def __init__(self, symbol, sector, price, debt_ratio, pe, eps, nav,
                 dividend_yield=0.0, earnings_yield=0.0, payout_ratio=0.0,
                 cfo=0.0):
        self.symbol = symbol
        self.sector = sector
        self.price = price
        self.debt_ratio = debt_ratio
        self.pe = pe
        self.eps = eps
        self.nav = nav
        self.dividend_yield = dividend_yield
        self.earnings_yield = earnings_yield
        self.payout_ratio = payout_ratio
        self.cfo = cfo

def fetch_dses_symbols():
    # DSE trading codes (not company abbreviations). Verified against dsebd.org.
    return [
        "GP", "SQURPHARMA", "OLYMPIC", "BATASHOE", "MARICO", "HEIDELBCEM", "LHB",
        "RECKITTBEN", "UNILEVERCL", "ISLAMIBANK", "BEXIMCO", "ACI", "ACMELAB", "RENATA"
    ]

def _to_float(text):
    """Parse a DSE numeric cell; '-', '', 'N/A' etc. become 0.0."""
    if not text:
        return 0.0
    cleaned = text.replace(',', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0

def _value_after_label(soup, label_regex):
    """Return the text of the cell immediately following the one matching label_regex."""
    label = soup.find(string=re.compile(label_regex, re.I))
    if not label:
        return None
    cell = label.find_parent(['td', 'th'])
    nxt = cell.find_next_sibling(['td', 'th']) if cell else None
    return nxt.get_text(' ', strip=True) if nxt else None

def _sector(soup):
    # The page has several "Sector*" strings (e.g. "Sectoral Median P/E"); match the exact cell.
    for cell in soup.find_all(['td', 'th']):
        if cell.get_text(strip=True) == 'Sector':
            nxt = cell.find_next(['td', 'th'])
            return nxt.get_text(strip=True) if nxt else "Unknown"
    return "Unknown"

def _latest_eps_nav(soup):
    """Pull EPS and NAV-per-share from the audited annual financials table (latest year)."""
    heading = soup.find('h2', string=re.compile('Financial Performance as per Audited', re.I))
    table = heading.find_next('table') if heading else None
    if not table:
        return 0.0, 0.0

    best_year, eps, nav = 0, 0.0, 0.0
    for row in table.find_all('tr'):
        cells = [td.get_text(' ', strip=True) for td in row.find_all('td')]
        # Data rows start with a 4-digit year, then 12 value columns.
        if len(cells) < 10 or not re.fullmatch(r'20\d{2}', cells[0]):
            continue
        year = int(cells[0])
        if year <= best_year:
            continue
        best_year = year
        # DSE splits EPS across "reported" and "continuing operations" columns and only
        # fills one of them, so take the first non-dash value across both groups.
        eps = next((_to_float(c) for c in cells[1:7] if c not in ('-', '')), 0.0)
        nav = next((_to_float(c) for c in cells[7:10] if c not in ('-', '')), 0.0)
    return eps, nav

def _debt_ratio(soup, price, shares):
    """AAOIFI-style leverage screen: interest-bearing debt / market cap.

    Loans are reported in millions; market cap is converted to the same unit.
    Returns 0.0 when market cap is unknown (avoids a divide-by-zero false pass).
    """
    text = soup.get_text(' ', strip=True)
    short_term = re.search(r'Short-term loan \(mn\)\s*([\d,\.]+)', text)
    long_term = re.search(r'Long-term loan \(mn\)\s*([\d,\.]+)', text)
    total_debt_mn = (_to_float(short_term.group(1)) if short_term else 0.0) + \
                    (_to_float(long_term.group(1)) if long_term else 0.0)
    market_cap_mn = price * shares / 1_000_000
    return total_debt_mn / market_cap_mn if market_cap_mn > 0 else 0.0

def get_stock_data(symbol):
    url = f"https://dsebd.org/displayCompany.php?name={symbol}"
    try:
        soup = BeautifulSoup(_fetch_html(url), 'html.parser')

        sector = _sector(soup)
        pe = _to_float(_value_after_label(soup, r'Current P/E Ratio using Basic EPS'))
        price = _to_float(_value_after_label(soup, r'Closing Price'))
        shares = _to_float(_value_after_label(soup, r'Total No\. of Outstanding Securities'))
        eps, nav = _latest_eps_nav(soup)
        debt_ratio = _debt_ratio(soup, price, shares)

        earnings_yield = (eps / price) * 100 if price > 0 else 0.0
        # "Cash Dividend" cell reads e.g. "215% 2025, 330% 2024, ..."; take the latest.
        # The percentage is of BDT 10 face value, so cash-per-share = pct/100 * 10.
        cash_div_cell = _value_after_label(soup, r'Cash Dividend') or ""
        pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', cash_div_cell)
        cash_per_share = float(pct_match.group(1)) / 100 * 10 if pct_match else 0.0
        dividend_yield = (cash_per_share / price) * 100 if price > 0 else 0.0
        # Share of earnings paid out as cash. Undefined (0.0) when EPS <= 0.
        payout_ratio = (cash_per_share / eps) * 100 if eps > 0 else 0.0

        return Stock(symbol, sector, price, round(debt_ratio, 3), pe, eps, nav,
                     round(dividend_yield, 4), round(earnings_yield, 2),
                     round(payout_ratio, 1))
    except Exception:
        return None

def filter_halal(stocks):
    haram_sectors = {"Tobacco", "Bank", "Financial", "Mutual Funds"}
    return [s for s in stocks
            if not any(h in s.sector for h in haram_sectors) and s.debt_ratio < 0.33]
