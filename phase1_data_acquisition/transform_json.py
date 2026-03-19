import json
import os

# Project paths relative to script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACQUISITION_JSON = os.path.join(BASE_DIR, "phase1_data_acquisition", "structured_funds.json")
ROOT_JSON = os.path.join(BASE_DIR, "structured_funds.json")

# Define the investment objectives for natural consistency
objectives = {
    "Kotak Large Cap Fund": "To generate long-term capital appreciation by investing predominantly in equity and equity-related securities of large-cap companies benchmarked against the Nifty 100 TRI.",
    "Kotak Midcap Fund": "To generate long-term capital appreciation by investing primarily in mid-cap companies. The fund follows the Nifty Midcap 150 TRI as its benchmark and invests at least 65% of its assets in mid-cap companies with strong growth potential.",
    "Kotak Small Cap Fund": "To generate long-term capital appreciation by investing predominantly in small-cap companies. The fund follows the Nifty Smallcap 250 TRI as its benchmark and invests at least 65% of its assets in equity and equity-related instruments of small-cap companies.",
    "HDFC Large Cap Fund": "To generate long-term capital appreciation by investing predominantly in large-cap companies. The fund follows the Nifty 100 TRI as its benchmark and invests primarily in well-established large-cap stocks.",
    "HDFC Mid Cap Fund": "To generate long-term capital appreciation by investing predominantly in mid-cap companies. The fund follows the Nifty Midcap 150 TRI as its benchmark and invests at least 65% of its assets in mid-cap companies with strong growth potential.",
    "HDFC Small Cap Fund": "To generate long-term capital appreciation by investing predominantly in small-cap companies. The fund follows the BSE 250 SmallCap TRI as its benchmark and invests at least 65% of its assets in small-cap stocks with strong growth potential.",
    "ICICI Prudential Large Cap Fund": "To generate long-term capital appreciation by investing predominantly in equity and equity-related securities of large-cap companies benchmarked against the Nifty 100 TRI.",
    "ICICI Prudential MidCap Fund": "To generate long-term capital appreciation by investing predominantly in equity and equity-related securities of mid-cap companies benchmarked against the Nifty Midcap 150 TRI.",
    "ICICI Prudential Smallcap Fund": "To generate long-term capital appreciation by investing predominantly in equity and equity-related securities of small-cap companies benchmarked against the Nifty Smallcap 250 TRI."
}

def transform_funds():
    if not os.path.exists(ACQUISITION_JSON):
        print(f"Error: {ACQUISITION_JSON} not found.")
        return

    with open(ACQUISITION_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        # 1. Remove "How to Download Statement"
        if "How to Download Statement" in entry:
            del entry["How to Download Statement"]

        # 2. Update Investment Objective
        name = entry.get("Fund Name")
        if name in objectives:
            entry["Investment Objective"] = objectives[name]

        # 3. Fix ICICI Prudential MidCap Fund Minimum Lumpsum
        if name == "ICICI Prudential MidCap Fund":
            entry["Minimum Lumpsum"] = "₹5000"

        # 4. Clean placeholders and replace unicode Rupee
        keys_to_delete = []
        for key, value in entry.items():
            if value is None or value == "" or value == "--":
                if key in ["Minimum Lumpsum", "Minimum SIP"]:
                    entry[key] = "N/A"
                elif key == "Portfolio Turnover":
                    entry[key] = "0.00%"
                else:
                    keys_to_delete.append(key)
                continue

            if isinstance(value, str):
                entry[key] = value.replace("\u20b9", "₹")
        
        for key in keys_to_delete:
            del entry[key]

    # Save to BOTH locations to keep system in sync
    for target in [ACQUISITION_JSON, ROOT_JSON]:
        with open(target, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Successfully updated {target}")

if __name__ == "__main__":
    transform_funds()
