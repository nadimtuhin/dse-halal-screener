# DSE Halal Compounding Screener

Automated CLI tool to identify Shariah-compliant (Halal) DSE stocks with strong fundamentals.

## Features
- Fetches real-time price & P/E from DSE official site.
- Filters debt-heavy/haram sectors (tobacco, banking, high-leverage).
- Screens for compounding metrics: Operating Cash Flow (CFO), P/E ratios.
- Automatable via cron/bi-weekly runs.

## Setup
```bash
cd projects/dse-halal-screener
pip install -e .
```

## Run Screener
```bash
python3 dse_halal_screener/cli.py --pe 15 --min-cf 1.0
```
