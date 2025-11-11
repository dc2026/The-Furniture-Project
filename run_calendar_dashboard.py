# Quick launcher for TFP Calendar Dashboard

import subprocess
import sys
import os

def run_calendar_dashboard():
    """Launch the TFP Calendar Dashboard"""
    print("🏠 THE FURNITURE PROJECT - CALENDAR DASHBOARD")
    print("=" * 50)
    print("🚀 Launching calendar dashboard...")
    print("📅 This mimics your current Google Calendar system")
    print("✨ With smart scheduling and route optimization")
    print()
    
    try:
        # Run the Streamlit dashboard
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "tfp_calendar_dashboard.py",
            "--server.port", "8502"  # Use different port to avoid conflicts
        ])
    except KeyboardInterrupt:
        print("\n👋 Calendar dashboard closed")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")
        print("\n🔧 Try running manually:")
        print("streamlit run tfp_calendar_dashboard.py")

if __name__ == "__main__":
    run_calendar_dashboard()