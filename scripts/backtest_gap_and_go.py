import os
import requests
import json
from datetime import datetime

API_KEY = os.getenv("POLYGON_API_KEY")
TEST_DATE = "2023-10-11"  # You can change this to a recent weekday
OUT_FILE = f"polygon_raw_{TEST_DATE}.json"

def fetch_grouped_data(date_str):
    url = (
        f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date_str}"
        f"?adjusted=true&include_otc=false&apiKey={API_KEY}"
    )
    print(f"[INFO] Requesting data for {date_str} with key: {API_KEY[:4]}...{API_KEY[-4:]}" if API_KEY else "[!] No API key set.")
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"[+] Retrieved {len(results)} tickers")
        if results:
            print(f"[+] Sample result: {results[0]}")
        with open(OUT_FILE, "w") as f:
            json.dump(data, f, indent=2)
            print(f"[+] Raw response saved to {OUT_FILE}")
    else:
        print(f"[!] Failed request: {response.status_code} - {response.text}")

if __name__ == "__main__":
    fetch_grouped_data(TEST_DATE)
