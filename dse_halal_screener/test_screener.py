from bs4 import BeautifulSoup
from dse_halal_screener.screener import _to_float, _latest_eps_nav, _sector

def test_to_float_handles_dse_junk():
    assert _to_float("1,234.5") == 1234.5
    assert _to_float("-") == 0.0
    assert _to_float(None) == 0.0

def test_latest_eps_nav_picks_latest_year_and_right_columns():
    # Mirrors dsebd.org: EPS lives in the "continuing operations" column, NAV two groups over.
    html = """
    <h2>Financial Performance as per Audited Financial Statements</h2>
    <table>
      <tr><td>2023</td><td>-</td><td>-</td><td>-</td><td>21.41</td><td>-</td><td>-</td>
          <td>129.95</td><td>-</td><td>-</td><td>1</td><td>2</td><td>3</td></tr>
      <tr><td>2024</td><td>-</td><td>-</td><td>-</td><td>23.61</td><td>-</td><td>-</td>
          <td>142.05</td><td>-</td><td>-</td><td>1</td><td>2</td><td>3</td></tr>
    </table>"""
    eps, nav = _latest_eps_nav(BeautifulSoup(html, 'html.parser'))
    assert eps == 23.61 and nav == 142.05

def test_sector_ignores_sectoral_median_pe():
    html = "<table><tr><td>Sectoral Median P/E</td><td>15</td></tr>" \
           "<tr><td>Sector</td><td>Pharmaceuticals &amp; Chemicals</td></tr></table>"
    assert _sector(BeautifulSoup(html, 'html.parser')) == "Pharmaceuticals & Chemicals"
