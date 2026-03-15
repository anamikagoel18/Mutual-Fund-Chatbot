import os
import sys
import subprocess
import time
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_pulse():
    start_time = time.time()
    start_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{start_dt}] --- Starting Data Refresh Pulse Cycle (Scheduler start time) ---")
    
    # 1. Scraping Phase
    print("\n[Phase 1/2] Scraping fresh data...")
    scraper_path = os.path.join("phase1_data_acquisition", "scraper.py")
    try:
        subprocess.run([sys.executable, scraper_path], check=True)
        scrape_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{scrape_dt}] Success: Data scraped and saved to structured_funds.json (Scraper completion)")
    except subprocess.CalledProcessError as e:
        print(f"Error during scraping: {e}")
        return
    
    # 2. Ingestion Phase
    print("\n[Phase 2/2] Ingesting data into Vector Store...")
    ingest_path = os.path.join("phase2_vector_store", "ingest.py")
    try:
        # ingest.py uses stable IDs with .add_documents() which performs an upsert logic in ChromaDB.
        subprocess.run([sys.executable, ingest_path], check=True)
        ingest_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ingest_dt}] Success: Vector DB update completed. (Vector DB update)")
    except subprocess.CalledProcessError as e:
        print(f"Error during ingestion: {e}")
        return
    
    end_time = time.time()
    duration = end_time - start_time
    end_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{end_dt}] --- Pulse Cycle Completed Successfully in {duration:.2f} seconds (Scheduler completion) ---")

if __name__ == "__main__":
    run_pulse()
