# setup_and_run.py
# One-click setup and launch for The Furniture Project Dashboard

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Packages installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install packages")
        return False

def run_dashboard():
    """Launch the Streamlit dashboard"""
    print("Launching TFP Dashboard...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "complete_tfp_dashboard.py"])
    except KeyboardInterrupt:
        print("\n👋 Dashboard closed")
    except Exception as e:
        print(f"❌ Error launching dashboard: {e}")

def main():
    print("🏠 THE FURNITURE PROJECT - SETUP & LAUNCH")
    print("=" * 50)
    
    # Install packages
    if install_requirements():
        print("\n🚀 Starting dashboard...")
        run_dashboard()
    else:
        print("\n❌ Setup failed. Please install packages manually:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()