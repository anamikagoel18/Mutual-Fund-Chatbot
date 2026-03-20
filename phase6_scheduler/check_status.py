import os
import json
import time
from datetime import datetime

def check_scheduler_status():
    print("==========================================")
    print("      MUTUAL FUND SCHEDULER STATUS        ")
    print("==========================================")

    # 1. Check Data Freshness
    json_path = "structured_funds.json"
    if os.path.exists(json_path):
        mtime = os.path.getmtime(json_path)
        last_update = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            fund_count = len(data)
            
        print(f"--- Local Data Status ---")
        print(f"   - Total Funds: {fund_count}")
        print(f"   - Last Local Update: {last_update}")
    else:
        print("--- structured_funds.json not found! ---")

    # 2. Check Workflow Configuration
    workflow_path = ".github/workflows/data_refresh.yml"
    if os.path.exists(workflow_path):
        print("\n--- GitHub Actions Configuration ---")
        with open(workflow_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                if "cron:" in line:
                    print(f"   - Schedule: {line.strip()}")
        print("   - Strategy: Atomic Multi-Phase Refresher")
    else:
        print("\n--- GitHub Workflow not found! ---")

    # 3. Remote Status Link
    print("\n--- GitHub Actions Logs ---")
    print("   https://github.com/anamikagoel18/Mutual-Fund-Chatbot/actions")
    
    print("\nTip: If you see a failure in Actions, look for the Phase (1, 2, or 3) with the Red Cross.")
    print("==========================================")

if __name__ == "__main__":
    check_scheduler_status()
