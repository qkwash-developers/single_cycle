import os
import requests
import time
import threading
import subprocess
from shared_memory_util import write_data_to_shared_memory
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class JobChecker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        
        # API configuration from environment variables
        self.api_base_url = os.getenv("API_BASE_URL")
        self.api_url = f"{self.api_base_url}/device/checkjobs"
        self.hub_id = os.getenv("HUB_ID")
        self.device_id = int(os.getenv("DEVICE_ID"))
        
        # Request configuration from environment variables
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", 10))  # default to 10 if not set
        self.check_interval = int(os.getenv("CHECK_INTERVAL", 5))    # default to 5 if not set
        
    def check_jobs(self):
        """
        Make API request to check for new jobs and update shared memory.
        """
        data = {
            "hubid": self.hub_id,
            "deviceid": self.device_id
        }
        
        try:
            # Make API request with timeout
            response = requests.post(
                self.api_url,
                json=data,
                timeout=self.request_timeout
            )
            
            if response.status_code == 200:
                # Process successful response
                response_data = response.json()

                device_status_raw = response_data.get('deviceStatus', "0")
                washModeValue = float(response_data.get('washModeValue', "0.0") or 0.0)

                # Convert deviceStatus to float if numeric; else use 1000.0
                try:
                    if device_status_raw.replace('.', '', 1).isdigit():
                        device_status = float(device_status_raw)
                    else:
                        device_status = 1000.0
                except ValueError:
                    device_status = 1000.0

                # Write to shared memory
                write_data_to_shared_memory("command_from_server", device_status)
                write_data_to_shared_memory("command_mode_from_server", washModeValue)

                # Restart service if command is 1000
                if device_status == 1000.0:
                    subprocess.run(["sudo", "systemctl", "restart", "run_python_programs.service"])

            elif response.status_code == 204:
                # No job available
                write_data_to_shared_memory("command_from_server", 1000.0)
                subprocess.run(["sudo", "systemctl", "restart", "run_python_programs.service"])
                
        except requests.exceptions.RequestException:
            pass
        except ValueError:
            pass
        except Exception:
            pass  # Fully silent for service mode

    def stop(self):
        """Stop the job checker thread."""
        self._stop_event.set()

    def run(self):
        """Main thread execution loop."""
        try:
            while not self._stop_event.is_set():
                self.check_jobs()
                time.sleep(self.check_interval)
        except Exception:
            self.stop()

def main():
    try:
        job_checker = JobChecker()
        job_checker.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        job_checker.stop()
        job_checker.join()

if __name__ == "__main__":
    main()
