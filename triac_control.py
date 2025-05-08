import RPi.GPIO as GPIO
import time
import threading
from shared_memory_util import read_data_from_shared_memory

class TriacController(threading.Thread):
    def __init__(self, triac_pin=24, input_pin=25):
        super().__init__()
        self.triac_pin = triac_pin
        self.input_pin = input_pin
        self.running = False
        
        # Thread synchronization
        self.triac_delay = 8000  # Default delay in microseconds
        self.delay_lock = threading.Lock()
        self.delay_updated = threading.Event()
        
        # Monitor thread
        self.monitor_thread = None
        
    def setup_gpio(self):
        """Initialize GPIO pins"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.triac_pin, GPIO.OUT)
        GPIO.setup(self.input_pin, GPIO.IN)
        
    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()
        
    def get_delay(self):
        """Get current TRIAC delay with thread safety"""
        with self.delay_lock:
            return self.triac_delay
            
    def set_delay(self, new_delay):
        """Set TRIAC delay with thread safety"""
        with self.delay_lock:
            self.triac_delay = new_delay
            self.delay_updated.set()
            
    def monitor_delay(self):
        """Monitor thread to watch for delay changes in shared memory"""
        while self.running:
            new_delay = read_data_from_shared_memory("triac_delay")
            current_delay = self.get_delay()
            
            if current_delay != new_delay:
                self.set_delay(new_delay)
                
            time.sleep(0.1)
            
    def stop(self):
        """Stop all threads"""
        self.running = False
        
    def run(self):
        """Main thread loop for TRIAC control"""
        try:
            self.setup_gpio()
            self.running = True
            
            # Start the monitor thread
            self.monitor_thread = threading.Thread(target=self.monitor_delay)
            self.monitor_thread.start()
            
            # Main TRIAC control loop
            while self.running:
                sensor_value = GPIO.input(self.input_pin)
                if sensor_value == GPIO.HIGH:
                    GPIO.output(self.triac_pin, GPIO.LOW)
                    
                    # Get current delay value
                    delay = self.get_delay()
                    time.sleep(delay / 1_000_000)  # Convert microseconds to seconds
                    
                    GPIO.output(self.triac_pin, GPIO.HIGH)
                    
        except Exception as e:
            print(f"Error in TRIAC controller: {e}")
            
        finally:
            if self.monitor_thread:
                self.monitor_thread.join()
            self.cleanup()
            
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        self.join()

# Example usage
if __name__ == "__main__":
    controller = TriacController()
    controller.start()
    try:
        while True:
            time.sleep(1)
    finally:
        controller.stop()
        controller.join()