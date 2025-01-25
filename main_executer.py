#!/usr/bin/env python3
import subprocess
import time
import os

def run_and_wait(script_name):
    """Run a script with nohup and wait for completion"""
    try:
        # Run the script with nohup
        log_file = f"{script_name.replace('.py', '')}.log"
        cmd = f"nohup python3 {script_name} > {log_file} 2>&1"
        
        # Execute the command
        process = subprocess.Popen(cmd, shell=True)
        
        # Wait for completion
        process.wait()
        
        # Check if process completed successfully
        if process.returncode == 0:
            print(f"{script_name} completed successfully")
            return True
        else:
            print(f"{script_name} failed with return code {process.returncode}")
            return False
            
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def main():
    # Record start time
    print("Starting execution at:", time.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Run main_stand.py
    if run_and_wait("main_stand.py"):
        # If successful, run main_compare.py
        run_and_wait("main_compare.py")
    
    # Record end time
    print("Execution finished at:", time.strftime("%Y-%m-%d %H:%M:%S"))

if __name__ == "__main__":
    main()