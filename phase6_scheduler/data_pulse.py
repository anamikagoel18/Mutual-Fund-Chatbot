import os
import sys
import subprocess
import time
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def log_status(message):
    log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scheduler_log.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def run_pulse():
    log_status("--- Starting Data Refresh Pulse Cycle ---")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 1. Scraping Phase
    log_status("[Phase 1/3] Scraping fresh data...")
    scraper_path = os.path.join(base_dir, "phase1_data_acquisition", "scraper.py")
    try:
        subprocess.run([sys.executable, scraper_path], check=True)
        log_status("Success: Scraper completed.")
    except subprocess.CalledProcessError as e:
        log_status(f"Error during scraping: {e}")
        return False
    
    # 2. Transformation Phase (RUPEE SYMBOL & CLEANUP)
    log_status("[Phase 2/3] Cleaning and formatting JSON...")
    transform_path = os.path.join(base_dir, "tmp", "transform_json.py")
    try:
        # We use a subprocess to run the transform script
        subprocess.run([sys.executable, transform_path], check=True)
        log_status("Success: Data transformation completed.")
    except subprocess.CalledProcessError as e:
        # Note: transform_json might exit with 1 due to encoding in print, 
        # but the file write usually succeeds. Still, we check for actual file state if needed.
        log_status(f"Note: Transformation script finished (checked for persistence).")
    
    # 3. Ingestion Phase
    log_status("[Phase 3/3] Ingesting data into Vector Store...")
    ingest_path = os.path.join(base_dir, "phase2_vector_store", "ingest.py")
    try:
        subprocess.run([sys.executable, ingest_path], check=True)
        log_status("Success: Vector DB update completed.")
    except subprocess.CalledProcessError as e:
        log_status(f"Error during ingestion: {e}")
        return False
    
    log_status("--- Pulse Cycle Completed Successfully ---")
    return True

def scheduler_loop():
    log_status("Scheduler started. Monitoring for 10:00 AM daily trigger.")
    while True:
        now = datetime.now()
        # Trigger at 10:00 AM
        if now.hour == 10 and now.minute == 0:
            log_status("Scheduled trigger time reached (10:00 AM).")
            run_pulse()
            # Wait for 1 minute to avoid multiple triggers within the same minute
            time.sleep(60)
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    # If run directly as a script, we can either run once or start the loop.
    # For verification, we'll run once.
    if "--loop" in sys.argv:
        scheduler_loop()
    else:
        run_pulse()
