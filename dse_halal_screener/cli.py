import argparse
import json
import sys
import os
import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dse_halal_screener.screener import Stock, filter_halal, fetch_dses_symbols, get_stock_data

def format_output(results, format_type):
    data = [vars(s) for s in results]
    if format_type == 'json':
        return json.dumps(data, indent=2)
    elif format_type == 'yaml':
        return yaml.dump(data)
    elif format_type == 'md':
        if not data: return "No results"
        headers = data[0].keys()
        rows = [f"| {' | '.join(headers)} |", f"| {' | '.join(['---'] * len(headers))} |"]
        for d in data:
            rows.append(f"| {' | '.join(str(d[k]) for k in headers)} |")
        return '\n'.join(rows)
    elif format_type == 'html':
        if not data: return "<p>No results</p>"
        headers = data[0].keys()
        rows = ["<table border='1'><thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>"]
        for d in data:
            rows.append("<tr>" + "".join(f"<td>{d[k]}</td>" for k in headers) + "</tr>")
        rows.append("</tbody></table>")
        return "".join(rows)
    else: # table format (plain ASCII)
        if not data: return "No results"
        headers = list(data[0].keys())
        col_widths = {h: max(len(h), max(len(str(d[h])) for d in data)) for h in headers}
        header_row = "  ".join(h.upper().ljust(col_widths[h]) for h in headers)
        separator = "  ".join("-" * col_widths[h] for h in headers)
        rows = [header_row, separator]
        for d in data:
            rows.append("  ".join(str(d[h]).ljust(col_widths[h]) for h in headers))
        return '\n'.join(rows)

def main():
    parser = argparse.ArgumentParser(description="DSE Halal Screener")
    parser.add_argument("--pe", type=float, default=20.0)
    parser.add_argument("--min-cf", type=float, default=0.0)
    parser.add_argument("--mock", action="store_true", help="Use sample data instead of fetching from DSE")
    parser.add_argument("-o", "--format", choices=['json', 'table', 'yaml', 'md', 'html'], default='table')
    args = parser.parse_args()

    if args.mock:
        stocks = [
            Stock(symbol="GP", sector="Telecommunication", price=41.5, debt_ratio=0.1, pe=12.29, eps=3.4, nav=25.0, cfo=5000),
            Stock(symbol="SQURPHARMA", sector="Pharmaceuticals", price=210.0, debt_ratio=0.15, pe=10.5, eps=20.0, nav=180.0, cfo=8000),
            Stock(symbol="BATBC", sector="Tobacco", price=520.0, debt_ratio=0.05, pe=9.5, eps=55.0, nav=450.0, cfo=12000),
            Stock(symbol="EBL", sector="Bank", price=28.0, debt_ratio=0.8, pe=6.2, eps=4.5, nav=20.0, cfo=3000),
        ]
    else:
        symbols = fetch_dses_symbols()
        stocks = [get_stock_data(sym) for sym in symbols]
        stocks = [s for s in stocks if s]

    filtered = filter_halal(stocks, min_cfo=args.min_cf)
    # pe <= 0 means "no P/E published" (negative/zero earnings), not "cheap" — exclude it.
    results = [s for s in filtered if 0 < s.pe <= args.pe]

    for s in results:
        s.dividend_yield = f"{s.dividend_yield}%"
        s.earnings_yield = f"{s.earnings_yield}%"

    print(format_output(results, args.format))

if __name__ == "__main__":
    main()
