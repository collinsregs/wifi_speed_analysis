#!/usr/bin/env python3
"""
WiFi Speed Test Logger
Run hourly speed tests and save results to a CSV file for analysis.
"""

import subprocess
import csv
import json
import time
import os
import sys
from datetime import datetime
import argparse
import platform

# Configuration
DEFAULT_OUTPUT_FILE = "speedtest_results.csv"
DEFAULT_INTERVAL = 3600  # 1 hour in seconds
CSV_FIELDS = ["timestamp", "download_mbps", "upload_mbps", "ping_ms", "jitter_ms", 
              "server_name", "server_id", "server_location", "isp"]

def check_speedtest_cli():
    """Check if speedtest CLI is installed and install if needed."""
    try:
        subprocess.run(['speedtest', '--version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        print("Speedtest CLI is installed.")
        return True
    except FileNotFoundError:
        print("Speedtest CLI not found. Please install it first.")
        print("\nInstallation instructions:")
        if platform.system() == "Linux":
            print("""
# For Debian/Ubuntu:
sudo apt-get install curl
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install speedtest

# For CentOS/RHEL:
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.rpm.sh | sudo bash
sudo yum install speedtest
""")
        elif platform.system() == "Darwin":  # macOS
            print("""
# Using Homebrew:
brew tap teamookla/speedtest
brew update
brew install speedtest
""")
        elif platform.system() == "Windows":
            print("""
# Using PowerShell (run as administrator):
Invoke-WebRequest -Uri https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.ps1 | Invoke-Expression
""")
        else:
            print("Visit: https://www.speedtest.net/apps/cli")
        
        return False

def run_speed_test():
    """Run speedtest and return results as dictionary."""
    print(f"Running speed test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    
    try:
        # Run speedtest with JSON output format and accept license/gdpr
        result = subprocess.run(
            ['speedtest', '--format=json', '--accept-license', '--accept-gdpr'],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse the JSON output
        data = json.loads(result.stdout)
        
        # Extract relevant information
        test_results = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "download_mbps": round(data["download"]["bandwidth"] * 8 / 1_000_000, 2),
            "upload_mbps": round(data["upload"]["bandwidth"] * 8 / 1_000_000, 2),
            "ping_ms": round(data["ping"]["latency"], 2),
            "jitter_ms": round(data.get("ping", {}).get("jitter", 0), 2),
            "server_name": data["server"]["name"],
            "server_id": data["server"]["id"],
            "server_location": f"{data['server']['location']}, {data['server']['country']}",
            "isp": data["isp"]
        }
        
        print(f"✓ Test complete! Download: {test_results['download_mbps']} Mbps, "
              f"Upload: {test_results['upload_mbps']} Mbps, "
              f"Ping: {test_results['ping_ms']} ms")
        
        return test_results
    
    except subprocess.CalledProcessError as e:
        print(f"Error running speedtest: {e}")
        print(f"Error output: {e.stderr}")
        return None
    except json.JSONDecodeError:
        print(f"Error parsing speedtest results")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def save_results(results, output_file):
    """Save test results to CSV file."""
    file_exists = os.path.isfile(output_file)
    
    try:
        with open(output_file, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(results)
        
        print(f"Results saved to {output_file}")
    except Exception as e:
        print(f"Error saving results: {e}")

def run_scheduled_tests(interval, output_file, single_test=False):
    """Run tests on a schedule or once if single_test is True."""
    if not check_speedtest_cli():
        return
    
    if single_test:
        results = run_speed_test()
        if results:
            save_results(results, output_file)
        return
    
    print(f"Starting scheduled speed tests every {interval} seconds.")
    print(f"Results will be saved to {output_file}")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            results = run_speed_test()
            if results:
                save_results(results, output_file)
            
            # Sleep until next test
            print(f"Waiting {interval} seconds until next test...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nStopping speed tests. Goodbye!")

def main():
    """Parse arguments and run program."""
    parser = argparse.ArgumentParser(description="Run scheduled WiFi speed tests and log results.")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT_FILE,
                        help=f"Output CSV file (default: {DEFAULT_OUTPUT_FILE})")
    parser.add_argument("-i", "--interval", type=int, default=DEFAULT_INTERVAL,
                        help=f"Interval between tests in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("-s", "--single", action="store_true",
                        help="Run a single test and exit")
    
    args = parser.parse_args()
    
    run_scheduled_tests(args.interval, args.output, args.single)

if __name__ == "__main__":
    main()