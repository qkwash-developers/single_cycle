import RPi.GPIO as GPIO
import time
import threading
from shared_memory_util import write_data_to_shared_memory

class SensorReader(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        
        # GPIO pin definitions
        self.pins = {
            'water_level': 18,  # GPIO 18 for water level sensor
            'door_status': 12   # GPIO 12 for door status
        }
        
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pins['water_level'], GPIO.IN)
        GPIO.setup(self.pins['door_status'], GPIO.IN)
        
        # Sensor reading configuration
        self.read_interval = 0.5  # seconds between readings
        self.pulse_timeout = 1.0  # timeout for pulse readings
        self.water_level_conversion_factor = 0.1  # adjust based on calibration

    def pulse_in(self, pin, level):
        """
        Measure the duration of a pulse on the specified pin.
        
        Args:
            pin: GPIO pin number
            level: Expected signal level (GPIO.HIGH or GPIO.LOW)
            
        Returns:
            Duration of the pulse in microseconds
        """
        start_time = time.time()
        
        # Wait for the signal to reach the expected level
        while GPIO.input(pin) != level:
            if time.time() - start_time > self.pulse_timeout:
                return 0
                
        # Measure the duration of the pulse
        start_time = time.time()
        while GPIO.input(pin) == level:
            if time.time() - start_time > self.pulse_timeout:
                return 0
                
        return (time.time() - start_time) * 1_000_000  # Convert to microseconds

    def read_pwm_frequency(self):
        """
        Read the PWM frequency from the water level sensor.
        
        Returns:
            Frequency in Hz, or 0 if measurement fails
        """
        high_duration = self.pulse_in(self.pins['water_level'], GPIO.HIGH)
        low_duration = self.pulse_in(self.pins['water_level'], GPIO.LOW)
        
        if high_duration == 0 or low_duration == 0:
            return 0
            
        period = high_duration + low_duration
        frequency = 1_000_000.0 / period  # Convert to Hz
        return frequency

    def read_water_level(self):
        """Read and process water level sensor data."""
        try:
            frequency = self.read_pwm_frequency()
            write_data_to_shared_memory("Pressure", frequency)
            
            # Convert frequency to water level
            water_level = frequency * self.water_level_conversion_factor
            write_data_to_shared_memory("Water_Level", water_level)
            
        except Exception as e:
            print(f"Error reading water level: {e}")

    def read_door_status(self):
        """Read and process door status sensor data."""
        try:
            status = GPIO.input(self.pins['door_status'])
            write_data_to_shared_memory("Door_Status", float(status))
            
        except Exception as e:
            print(f"Error reading door status: {e}")

    def stop(self):
        """Stop the sensor reading thread."""
        self._stop_event.set()

    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            GPIO.cleanup()
        except Exception as e:
            print(f"Error during GPIO cleanup: {e}")

    def run(self):
        """Main thread execution loop."""
        try:
            while not self._stop_event.is_set():
                # Read all sensors
                self.read_water_level()
                self.read_door_status()
                
                # Wait before next reading
                time.sleep(self.read_interval)
                
        except Exception as e:
            print(f"Error in sensor reading thread: {e}")
            self.stop()
        finally:
            self.cleanup()

def main():
    try:
        # Initialize and start sensor reader
        sensor_reader = SensorReader()
        sensor_reader.start()

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    finally:
        # Clean shutdown
        sensor_reader.stop()
        sensor_reader.join()

if __name__ == "__main__":
    main()