#!/usr/bin/env python3
"""
Monitor LangSmith for new traces
"""
import os
import time
from datetime import datetime, timezone
from langsmith import Client

# Initialize client
client = Client()
project_name = "faltuai-fun"

def check_for_traces():
    """Check for recent traces in the last minute"""
    try:
        # Get traces from the last 2 minutes
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time.replace(second=current_time.second-120)
        
        print(f"Checking for traces after {cutoff_time}")
        
        # List recent runs
        runs = list(client.list_runs(
            project_name=project_name,
            start_time=cutoff_time,
            limit=10
        ))
        
        print(f"Found {len(runs)} recent runs:")
        for run in runs:
            print(f"  - {run.id}: {run.name} ({run.start_time})")
            if hasattr(run, 'inputs'):
                print(f"    Inputs: {str(run.inputs)[:100]}...")
            if hasattr(run, 'outputs'):
                print(f"    Outputs: {str(run.outputs)[:100]}...")
            print()
            
        return len(runs)
        
    except Exception as e:
        print(f"Error checking traces: {e}")
        return 0

if __name__ == "__main__":
    print("Starting LangSmith trace monitor...")
    print(f"Project: {project_name}")
    print("Checking for traces every 30 seconds...")
    
    while True:
        trace_count = check_for_traces()
        print(f"Checked at {datetime.now()} - Found {trace_count} traces")
        print("-" * 50)
        time.sleep(30)