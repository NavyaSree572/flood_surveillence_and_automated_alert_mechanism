import subprocess
import time
import sys

def launch():
    print("🚀 Initializing Flood Guardian Ecosystem...")
    
    # 1. Initialize Database
    subprocess.run([sys.executable, "database_manager.py"])
    print("✅ Database Ready.")

    # 2. Start AI Tracking Service
    print("🧠 Starting AI Tracking...")
    tracker = subprocess.Popen([sys.executable, "tracking_reid.py"])

    # 3. Start Streamlit Dashboard
    print("💻 Starting Dashboard...")
    dashboard = subprocess.Popen(["streamlit", "run", "app_interface.py"])

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all services...")
        tracker.terminate()
        dashboard.terminate()

if __name__ == "__main__":
    launch()