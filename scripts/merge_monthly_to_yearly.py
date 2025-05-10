# scripts/merge_monthly_to_yearly.py

import os
import pandas as pd
from glob import glob

DATA_DIR = os.path.join(os.path.dirname(__file__), '../data')
OUTPUT_DIR = DATA_DIR  # Output to same location

def merge_monthly_csvs():
    files = sorted(glob(os.path.join(DATA_DIR, '*-*-data.csv')))
    year_to_dfs = {}

    for file_path in files:
        filename = os.path.basename(file_path)
        year = filename[:4]

        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                if year not in year_to_dfs:
                    year_to_dfs[year] = []
                year_to_dfs[year].append(df)
        except Exception as e:
            print(f"[!] Failed to read {filename}: {e}")

    for year, dfs in year_to_dfs.items():
        combined = pd.concat(dfs, ignore_index=True)
        out_path = os.path.join(OUTPUT_DIR, f'{year}.csv')
        combined.to_csv(out_path, index=False)
        print(f"[+] Saved {len(combined)} rows to {out_path}")

if __name__ == "__main__":
    print("[*] Merging monthly CSVs into yearly files...")
    merge_monthly_csvs()
