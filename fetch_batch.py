import os
import sys
import datetime
import pandas as pd
import yfinance as yf

HEADERS = ["timestamp", "datetime_utc", "open", "high", "low", "close", "volume"]

COMPANIES = {
    "360ONE": ("360 ONE WAM Ltd", "360ONE.NS"),
    "APLAPOLLO": ("APL Apollo Tubes Ltd", "APLAPOLLO.NS"),
    "AUBANK": ("AU Small Finance Bank Ltd", "AUBANK.NS"),
    "ATGL": ("Adani Total Gas Ltd", "ATGL.NS"),
    "ABCAPITAL": ("Aditya Birla Capital Ltd", "ABCAPITAL.NS"),
    "APARINDS": ("Apar Industries Ltd", "APARINDS.NS"),
    "ASHOKLEY": ("Ashok Leyland Ltd", "ASHOKLEY.NS"),
    "ASTRAL": ("Astral Ltd", "ASTRAL.NS"),
    "AUROPHARMA": ("Aurobindo Pharma Ltd", "AUROPHARMA.NS"),
    "BANKINDIA": ("Bank of India", "BANKINDIA.NS"),
    "MAHABANK": ("Bank of Maharashtra", "MAHABANK.NS"),
    "BDL": ("Bharat Dynamics Ltd", "BDL.NS"),
    "BHARATFORG": ("Bharat Forge Ltd", "BHARATFORG.NS"),
    "BHEL": ("Bharat Heavy Electricals Ltd", "BHEL.NS"),
    "GROWW": ("Billionbrains Garage Ventures Ltd", "GROWW.NS"),
    "BIOCON": ("Biocon Ltd", "BIOCON.NS"),
    "BLUESTARCO": ("Blue Star Ltd", "BLUESTARCO.NS"),
    "COCHINSHIP": ("Cochin Shipyard Ltd", "COCHINSHIP.NS"),
    "COFORGE": ("Coforge Ltd", "COFORGE.NS"),
    "COLPAL": ("Colgate Palmolive (India) Ltd", "COLPAL.NS"),
    "CONCOR": ("Container Corporation of India Ltd", "CONCOR.NS"),
    "DABUR": ("Dabur India Ltd", "DABUR.NS"),
    "DIXON": ("Dixon Technologies (India) Ltd", "DIXON.NS"),
    "EXIDEIND": ("Exide Industries Ltd", "EXIDEIND.NS"),
    "NYKAA": ("FSN E-Commerce Ventures Ltd", "NYKAA.NS"),
    "FEDERALBNK": ("Federal Bank Ltd", "FEDERALBNK.NS"),
    "FORTIS": ("Fortis Healthcare Ltd", "FORTIS.NS"),
    "GVT_D": ("GE Vernova T&D India Ltd", "GVT&D.NS"),
    "GMRAIRPORT": ("GMR Airports Ltd", "GMRAIRPORT.NS"),
    "GLENMARK": ("Glenmark Pharmaceuticals Ltd", "GLENMARK.NS")
}

now = datetime.datetime.now(datetime.timezone.utc)
print(f"=== India Equities Batch 91-120 Ingestion (UTC Now: {now.strftime('%Y-%m-%d %H:%M:%S')}) ===")

total_new_candles = 0

for folder_name, (full_name, yf_ticker) in COMPANIES.items():
    print(f"\nProcessing {folder_name} ({yf_ticker})...")
    try:
        ticker = yf.Ticker(yf_ticker)
        df = ticker.history(period="7d", interval="1m")
    except Exception as e:
        print(f"Error fetching {yf_ticker}: {e}")
        continue

    if df is None or df.empty:
        print(f"No data returned for {yf_ticker}")
        continue

    rows = []
    for idx, row in df.iterrows():
        ts = int(idx.timestamp() * 1000)
        dt_utc = idx.tz_convert("UTC").strftime("%Y-%m-%d %H:%M:%S")
        rows.append([ts, dt_utc, float(row["Open"]), float(row["High"]), float(row["Low"]), float(row["Close"]), float(row["Volume"])])

    incoming_df = pd.DataFrame(rows, columns=HEADERS)
    incoming_df.drop_duplicates(subset=["timestamp"], inplace=True)
    incoming_df.sort_values(by="timestamp", inplace=True)

    company_root = os.path.join(folder_name, "1m")
    os.makedirs(company_root, exist_ok=True)

    # Symbol README
    with open(os.path.join(company_root, "README.md"), "w") as f:
        f.write(f"# {full_name} ({folder_name}) 1-Minute Historical Kline Dataset\n\n- **Symbol:** `{folder_name}` (NSE: `{yf_ticker}`)\n- **Market:** National Stock Exchange of India (NSE)\n- **Timeframe:** 1 Minute (`1m`)\n- **Trading Hours:** Monday - Friday 09:15 to 15:30 IST (03:45 to 10:00 UTC)\n- **Schema:** `timestamp, datetime_utc, open, high, low, close, volume`\n")

    # Group by date YYYY-MM-DD
    grouped = incoming_df.groupby(incoming_df["datetime_utc"].str[:10])
    for day_str, grp in grouped:
        y, m = day_str[:4], day_str[5:7]
        target_dir = os.path.join(company_root, y, m)
        os.makedirs(target_dir, exist_ok=True)
        csv_file = os.path.join(target_dir, f"{folder_name}_1m_{day_str}.csv")

        if os.path.exists(csv_file):
            try:
                existing_df = pd.read_csv(csv_file)
                combined = pd.concat([existing_df, grp], ignore_index=True)
                combined.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
                combined.sort_values(by="timestamp", inplace=True)
                combined[HEADERS].to_csv(csv_file, index=False)
            except Exception:
                grp[HEADERS].to_csv(csv_file, index=False)
        else:
            grp[HEADERS].to_csv(csv_file, index=False)

    print(f"Saved {len(incoming_df):,} candles across {len(grouped)} trading days for {folder_name}.")
    total_new_candles += len(incoming_df)

# Dynamic Master README Calculation
total_csv_files = 0
total_candles_all = 0
for root, dirs, files in os.walk("."):
    for f in files:
        if f.endswith(".csv") and not f.startswith("."):
            total_csv_files += 1
            with open(os.path.join(root, f), "r") as fl:
                total_candles_all += max(0, sum(1 for _ in fl) - 1)

master_readme = f"""# India Public Equities (Constituents 91 to 120) - 1-Minute Historical Kline Archive

An institutional-grade, open-source archive of cleaned, standardized, and validated **1-minute intraday historical candlestick data** for **India's Top Liquid Companies (Batch 91 to 120)** with daily automated cloud ingestion.

---

## 🏛️ Directory Architecture & Strict Date-Wise Hierarchy

Every stock is strictly organized into daily CSVs partitioned by Year/Month/Date:

```text
India-Stocks-91-120-Historical-Data/
├── 360ONE/
│   └── 1m/
│       ├── README.md
│       └── 2026/
│           └── 10/
│               ├── 360ONE_1m_2026-10-01.csv
│               ├── 360ONE_1m_2026-10-05.csv
│               └── 360ONE_1m_2026-10-09.csv
├── DABUR/
│   └── 1m/...
└── ... [All 30 Companies]
```

---

## 📊 Dataset Overview
- **Constituents:** 30 Benchmark Companies (Rank 91 to 120)
- **Timeframe:** 1 Minute (`1m`)
- **Total Archived Daily Files:** `{total_csv_files}` sessions
- **Total 1-Minute Candles:** `{total_candles_all:,}` candles
- **Last Ingested:** `{now.strftime('%Y-%m-%d %H:%M:%S')} UTC`
- **Trading Sessions:** Monday – Friday, 09:15 to 15:30 IST (03:45 to 10:00 UTC)

---

## 📑 Data Schema (Uniform Across All Files)

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `timestamp` | `int64` | Candle open time in Unix milliseconds (UTC) | `1791517500000` |
| `datetime_utc` | `string` | Standard ISO human-readable UTC timestamp | `2026-10-09 03:45:00` |
| `open` | `float64` | Opening price in INR | `532.10` |
| `high` | `float64` | Highest price reached during the 1-minute window | `533.40` |
| `low` | `float64` | Lowest price reached during the 1-minute window | `531.80` |
| `close` | `float64` | Closing price of the 1-minute candle | `532.90` |
| `volume` | `float64` | Cumulative volume traded in the 1-minute candle | `5610` |

---

## ⚡ 1-Line Pandas Stream Loader (No Clone Required)

Stream any stock's 1-minute data directly from GitHub's raw CDN into Pandas in 1 second:

```python
import pandas as pd

# Load 360ONE 1-minute data for October 09, 2026
url = "https://raw.githubusercontent.com/parshant65-lang/India-Stocks-91-120-Historical-Data/main/360ONE/1m/2026/10/360ONE_1m_2026-10-09.csv"
df = pd.read_csv(url)
print(df.head())
```

---

## 🔄 Daily Automated Cloud Ingestion
A GitHub Actions workflow runs every weekday post-market (**Monday to Friday at 16:30 IST / 11:00 UTC**) to query Yahoo Finance, slice newly closed 1-minute sessions into daily CSVs, de-duplicate timestamps, and commit updates automatically.
"""

with open("README.md", "w") as f:
    f.write(master_readme)

print("\n🎉 Batch 91-120 ingestion and master README generation complete!")
