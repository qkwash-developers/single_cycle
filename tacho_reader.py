import threading
import time
import pigpio
from shared_memory_util import write_data_to_shared_memory

class TachoSensorThread(threading.Thread):
    def __init__(self, gpio_pin=16):
        super().__init__()
        self.gpio_pin = gpio_pin
        self.running = False
        self.pulse_count = 0
        self.pi = None
        self.last_time = time.time()
        
    def count_pulse(self, gpio, level, tick):
        """Callback function to count pulses"""
        self.pulse_count += 1
        
    def setup_gpio(self):
        """Initialize GPIO and set up callback"""
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Failed to connect to pigpio daemon")
            
        self.pi.set_mode(self.gpio_pin, pigpio.INPUT)
        self.callback = self.pi.callback(
            self.gpio_pin, 
            pigpio.RISING_EDGE, 
            self.count_pulse
        )
        
    def cleanup(self):
        """Clean up GPIO resources"""
        if self.pi:
            self.callback.cancel()
            self.pi.stop()
            
    def stop(self):
        """Stop the sensor thread"""
        self.running = False
        
    def run(self):
        """Main thread loop"""
        try:
            self.setup_gpio()
            self.running = True
            
            while self.running:
                time.sleep(1)  # Measurement interval
                
                current_time = time.time()
                elapsed_time = current_time - self.last_time
                self.last_time = current_time
                
                # Calculate frequency and RPM
                frequency = self.pulse_count / elapsed_time
                rpm = frequency * 60.0
                
                # Write to shared memory
                write_data_to_shared_memory("taccosensor", frequency)
                
                # Reset pulse count for next interval
                self.pulse_count = 0
                
        except Exception as e:
            print(f"Error in TachoSensor thread: {e}")
            
        finally:
            self.cleanup()

# Example usage
if __name__ == "__main__":
    try:
        # Create and start the sensor thread
        tacho_sensor = TachoSensorThread()
        tacho_sensor.start()
        
        # Keep main thread running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping sensor measurement...")
        tacho_sensor.stop()
        tacho_sensor.join()
        print("Sensor thread stopped cleanly")