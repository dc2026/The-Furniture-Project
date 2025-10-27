# run_all.py
# Execute complete backend pipeline in sequence

import subprocess
import sys
import os

def run_script(script_name):
    """Run a Python script and display results"""
    print(f"\n{'='*50}")
    print(f"RUNNING: {script_name}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("WARNINGS:", result.stderr)
        print(f"✓ {script_name} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {script_name} failed:")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"✗ {script_name} not found")
        return False

def main():
    """Run complete backend pipeline"""
    print("FURNITURE PROJECT BACKEND - COMPLETE PIPELINE")
    print("=" * 60)
    
    # List of scripts to run in order
    scripts = [
        "clean_data.py",
        "route_assignment.py", 
        "daily_truck_scheduler.py"
    ]
    
    success_count = 0
    
    for script in scripts:
        if run_script(script):
            success_count += 1
        else:
            print(f"\nPipeline stopped due to error in {script}")
            break
    
    # Final summary
    print(f"\n{'='*60}")
    print("PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Scripts executed: {success_count}/{len(scripts)}")
    
    if success_count == len(scripts):
        print("✓ All scripts completed successfully!")
        print("\nGenerated files:")
        data_files = [
            "data/master_requests.csv",
            "data/complete_route_assignments.csv", 
            "data/truck_route_summary.csv",
            "data/daily_truck_schedule.csv",
            "data/daily_summary.csv"
        ]
        
        for file in data_files:
            if os.path.exists(file):
                print(f"  ✓ {file}")
            else:
                print(f"  ✗ {file} (missing)")
        
        print(f"\nBackend ready for dashboard integration!")
    else:
        print("✗ Pipeline incomplete - check errors above")

if __name__ == "__main__":
    main()