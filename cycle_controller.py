import pigpio
import time
import threading
from shared_memory_util import create_shared_memory, read_data_from_shared_memory, write_data_to_shared_memory
import requests
import json
import RPi.GPIO as GPIO
from datetime import datetime
import threading




class RelayController(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        
        # Define GPIO pins
        self.pins = {
            'relay0': 17,
            'relay1': 27,
            'relay2': 22,
            'relay3': 23,
            'inlet2': 6,
            'inlet1': 13,
            'drain': 19,
            'door': 5
        }
        
        # Initialize pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("Unable to connect to pigpio daemon")
            
        # Initialize all pins to LOW
        for pin in self.pins.values():
            self.pi.write(pin, pigpio.LOW)
            
        # Command mapping
        self.command_map = {
            1.0: self.chCommand,
            2.0: self.clCommand,
            3.0: self.ahCommand,
            4.0: self.alCommand,
            5.0: self.stCommand,
            6.0: self.inlet2HCommand,
            7.0: self.inlet2LCommand,
            8.0: self.inlet1HCommand,
            9.0: self.inlet1LCommand,
            10.0: self.drainHCommand,
            11.0: self.drainLCommand,
            12.0: self.doorHCommand,
            13.0: self.doorLCommand,
            14.0: self.exit_handler
        }

    def chCommand(self):
        self.pi.write(self.pins['relay1'], pigpio.LOW)
        self.pi.write(self.pins['relay2'], pigpio.LOW)
        self.pi.write(self.pins['relay3'], pigpio.LOW)
        self.pi.write(self.pins['relay0'], pigpio.HIGH)

    def clCommand(self):
        self.pi.write(self.pins['relay1'], pigpio.HIGH)
        self.pi.write(self.pins['relay2'], pigpio.LOW)
        self.pi.write(self.pins['relay3'], pigpio.LOW)
        self.pi.write(self.pins['relay0'], pigpio.HIGH)

    def ahCommand(self):
        self.pi.write(self.pins['relay1'], pigpio.LOW)
        self.pi.write(self.pins['relay2'], pigpio.HIGH)
        self.pi.write(self.pins['relay3'], pigpio.HIGH)
        self.pi.write(self.pins['relay0'], pigpio.HIGH)

    def alCommand(self):
        self.pi.write(self.pins['relay1'], pigpio.HIGH)
        self.pi.write(self.pins['relay2'], pigpio.HIGH)
        self.pi.write(self.pins['relay3'], pigpio.HIGH)
        self.pi.write(self.pins['relay0'], pigpio.HIGH)

    def stCommand(self):
        self.pi.write(self.pins['relay0'], pigpio.LOW)

    def inlet2HCommand(self):
        self.pi.write(self.pins['inlet2'], pigpio.HIGH)

    def inlet2LCommand(self):
        self.pi.write(self.pins['inlet2'], pigpio.LOW)

    def inlet1HCommand(self):
        self.pi.write(self.pins['inlet1'], pigpio.HIGH)

    def inlet1LCommand(self):
        self.pi.write(self.pins['inlet1'], pigpio.LOW)

    def drainHCommand(self):
        self.pi.write(self.pins['drain'], pigpio.HIGH)

    def drainLCommand(self):
        self.pi.write(self.pins['drain'], pigpio.LOW)

    def doorHCommand(self):
        self.pi.write(self.pins['door'], pigpio.HIGH)
        time.sleep(0.2)
        self.pi.write(self.pins['door'], pigpio.LOW)
        write_data_to_shared_memory("relay_command", 13.0)

    def doorLCommand(self):
        self.pi.write(self.pins['door'], pigpio.LOW)

    def exit_handler(self):
        """Set all relay pins to LOW state on exit."""
        for pin in self.pins.values():
            self.pi.write(pin, pigpio.LOW)
        write_data_to_shared_memory("relay_command", 0.0)

    def stop(self):
        """Stop the thread."""
        self._stop_event.set()

    def run(self):
        """Main thread loop."""
        while not self._stop_event.is_set():
            command_value = read_data_from_shared_memory("relay_command")
            command = self.command_map.get(command_value)
            
            if command:
                print(f"Executing command: {command.__name__}")
                command()
            else:
                print(f"Unknown command value received: {command_value}")
            
            time.sleep(1)

class SharedMemoryManager(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        
        self.shared_memory_names = [
            "relay_command",
            "taccosensor",
            "doorssensor",
            "Pressure",
            "Water_Level",
            "Door_Status",
            "triac_delay",
            "command_from_server",
            "command_mode_from_server",
        ]

    def initialize_shared_memory(self):
        """Initialize all shared memory segments."""
        for name in self.shared_memory_names:
            try:
                create_shared_memory(name, 4)
                print(f"Shared memory '{name}' initialized.")
            except Exception as e:
                print(f"Failed to initialize shared memory '{name}': {e}")
        write_data_to_shared_memory("relay_command", 14.0)
        write_data_to_shared_memory("taccosensor", 0.0)
        write_data_to_shared_memory("doorssensor", 0.0)
        write_data_to_shared_memory("Pressure", 0.0)
        write_data_to_shared_memory("Water_Level", 0.0)
        write_data_to_shared_memory("Door_Status", 0.0)
        write_data_to_shared_memory("triac_delay", 8000.0)
        write_data_to_shared_memory("command_from_server", 1000.0)
        write_data_to_shared_memory("command_mode_from_server", 0.0)


    def stop(self):
        """Stop the thread."""
        self._stop_event.set()

    def run(self):
        """Main thread loop."""
        self.initialize_shared_memory()
        while not self._stop_event.is_set():
            # Add any periodic shared memory operations here
            time.sleep(1)





class WashingMachineController(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        
        # Instance variables for shared memory values
        self.door_status = None
        self.triac_delay = None
        self.taccosensor = None
        self.water_level = None
        self.command = 1000.0
        self.command_mode = 0.0
        
        # API configuration
        self.hub_id = "17348502838715973"
        self.device_id = 1000
        self.api_base_url = "http://srv630050.hstgr.cloud:3000/api/users"

    def update_ready(self):
        url = f"{self.api_base_url}/updateReady"
        data = {
            "hubid": self.hub_id,
            "deviceid": self.device_id
        }
        try:
            requests.post(url, json=data)
        except Exception:
            pass

    def update_progress(self, progress):
        url = f"{self.api_base_url}/updateProgress"
        data = {
            "hubid": self.hub_id,
            "deviceid": self.device_id,
            "progress": progress
        }
        try:
            requests.post(url, json=data)
        except Exception:
            pass

    def close_door(self):
        write_data_to_shared_memory("relay_command", 12.0)
        time.sleep(10)
        write_data_to_shared_memory("relay_command", 12.0)
        time.sleep(4)

    def open_door(self):
        write_data_to_shared_memory("relay_command", 12.0)
        time.sleep(4)

    def drain_water(self, time_of_job):
        write_data_to_shared_memory("relay_command", 10.0)
        time.sleep(time_of_job)
        write_data_to_shared_memory("relay_command", 11.0)
        time.sleep(1)

    def load_water(self, time_of_job):
        write_data_to_shared_memory("relay_command", 6.0)
        time.sleep(1)
        write_data_to_shared_memory("relay_command", 8.0)
        time.sleep(time_of_job)
        write_data_to_shared_memory("relay_command", 7.0)
        time.sleep(1)
        write_data_to_shared_memory("relay_command", 9.0)
        time.sleep(1)

    def check_and_load_water(self, target_level):
        write_data_to_shared_memory("relay_command", 6.0)
        time.sleep(1)
        write_data_to_shared_memory("relay_command", 8.0)
        while self.water_level > target_level:
            time.sleep(0.2)
        write_data_to_shared_memory("relay_command", 7.0)
        time.sleep(1)
        write_data_to_shared_memory("relay_command", 9.0)
        time.sleep(1)

    def send_rpm(self, rpm_input):
        write_data_to_shared_memory("triac_delay", float(rpm_input))

    def rpm_leveler(self, required_rpm):
        req_rpm_input = self.triac_delay
        while True:
            if (required_rpm - self.taccosensor) >= 10:
                req_rpm_input -= 30
            elif (required_rpm - self.taccosensor) <= -10:
                req_rpm_input += 30
            else:
                break
            self.send_rpm(req_rpm_input)
            time.sleep(1)

    def stop_spin(self):
        write_data_to_shared_memory("relay_command", 5.0)
        time.sleep(5)
        self.send_rpm(8000)

    def set_cl_direction(self):
        write_data_to_shared_memory("relay_command", 1.0)
        time.sleep(1)

    def set_al_direction(self):
        write_data_to_shared_memory("relay_command", 3.0)
        time.sleep(1)

    def drum_rotation_pattern_one(self):
        start_time = time.time()
        while (time.time() - start_time < 300):
            self.set_cl_direction()
            self.rpm_leveler(30)
            time.sleep(15)
            self.stop_spin()

            self.set_al_direction()
            self.rpm_leveler(30)
            time.sleep(15)
            self.stop_spin()

    def drum_rotation_pattern_two(self):
        start_time = time.time()
        while (time.time() - start_time < 300):
            self.set_cl_direction()
            self.rpm_leveler(40)
            time.sleep(15)
            self.stop_spin()

            self.set_al_direction()
            self.rpm_leveler(40)
            time.sleep(15)
            self.stop_spin()

    def cycle_end(self):
        write_data_to_shared_memory("relay_command", 14.0)

    def run_washing_cycle(self):
        while not self._stop_event.is_set():
            try:
                # quick wash
                if self.command_mode ==0.0:
                    print("quick wash\n")
                    if self.command <= 0.0:
                        time.sleep(10)
                        self.close_door()
                        self.update_progress("05")
                        write_data_to_shared_memory("command_from_server", 5.0)

                    elif self.command <= 5.0:
                        self.drain_water(10)
                        self.update_progress("10")
                        write_data_to_shared_memory("command_from_server", 10.0)

                    elif self.command <= 10.0:
                        self.check_and_load_water(13)
                        self.update_progress("15")
                        write_data_to_shared_memory("command_from_server", 15.0)

                    elif self.command <= 15.0:
                        self.send_rpm(8000)
                        self.drum_rotation_pattern_one()
                        self.update_progress("20")
                        write_data_to_shared_memory("command_from_server", 20.0)

                    elif self.command <= 20.0:
                        self.check_and_load_water(13)
                        self.drain_water(45)
                        self.update_progress("39")
                        write_data_to_shared_memory("command_from_server", 39.0)

                    elif self.command <= 39.0:
                        self.check_and_load_water(13)
                        self.update_progress("68")
                        write_data_to_shared_memory("command_from_server", 68.0)

                    elif self.command <= 68.0:
                        self.send_rpm(8000)
                        self.drum_rotation_pattern_two()
                        self.update_progress("80")
                        write_data_to_shared_memory("command_from_server", 80.0)

                    elif self.command <= 80.0:
                        self.check_and_load_water(13)
                        self.update_progress("90")
                        write_data_to_shared_memory("command_from_server", 90.0)

                    elif self.command <= 90.0:
                        self.drain_water(45)
                        self.update_progress("99")
                        write_data_to_shared_memory("command_from_server", 99.0)

                    elif self.command <= 99.0:
                        self.open_door()
                        self.update_ready()
                        write_data_to_shared_memory("command_from_server", 1000.0)
                        self.cycle_end()
                    time.sleep(1)



                # heavy wash
                elif self.command_mode ==1.0:
                    print("heavy wash\n")
                    if self.command <= 0.0:
                        time.sleep(10)
                        self.close_door()
                        self.update_progress("05")
                        write_data_to_shared_memory("command_from_server", 5.0)

                    elif self.command <= 5.0:
                        self.drain_water(10)
                        self.update_progress("10")
                        write_data_to_shared_memory("command_from_server", 10.0)

                    elif self.command <= 10.0:
                        self.check_and_load_water(13)
                        self.update_progress("15")
                        write_data_to_shared_memory("command_from_server", 15.0)

                    elif self.command <= 15.0:
                        self.send_rpm(8000)
                        self.drum_rotation_pattern_one()
                        self.update_progress("20")
                        write_data_to_shared_memory("command_from_server", 20.0)

                    elif self.command <= 20.0:
                        self.check_and_load_water(13)
                        self.drain_water(45)
                        self.update_progress("39")
                        write_data_to_shared_memory("command_from_server", 39.0)

                    elif self.command <= 39.0:
                        self.check_and_load_water(13)
                        self.update_progress("68")
                        write_data_to_shared_memory("command_from_server", 68.0)

                    elif self.command <= 68.0:
                        self.send_rpm(8000)
                        self.drum_rotation_pattern_two()
                        self.update_progress("80")
                        write_data_to_shared_memory("command_from_server", 80.0)

                    elif self.command <= 80.0:
                        self.check_and_load_water(13)
                        self.update_progress("90")
                        write_data_to_shared_memory("command_from_server", 90.0)

                    elif self.command <= 90.0:
                        self.drain_water(45)
                        self.update_progress("99")
                        write_data_to_shared_memory("command_from_server", 99.0)

                    elif self.command <= 99.0:
                        self.open_door()
                        self.update_ready()
                        write_data_to_shared_memory("command_from_server", 1000.0)
                        self.cycle_end()
                    time.sleep(1)

            except Exception as e:
                print(f"Error in washing cycle: {e}")
                time.sleep(1)



    def update_shared_memory_values(self):
        """Update all shared memory values."""
        while not self._stop_event.is_set():
            try:
                self.door_status = read_data_from_shared_memory("Door_Status")
                self.triac_delay = read_data_from_shared_memory("triac_delay")
                self.taccosensor = read_data_from_shared_memory("taccosensor")
                self.water_level = read_data_from_shared_memory("Pressure")
                self.command = read_data_from_shared_memory("command_from_server")
                self.command_mode = read_data_from_shared_memory("command_mode_from_server")

            except Exception as e:
                print(f"Error reading shared memory: {e}")
            time.sleep(1)

    def stop(self):
        """Stop the thread."""
        self._stop_event.set()

    def run(self):
        """Main thread execution."""
        # Start shared memory update thread
        shared_memory_thread = threading.Thread(
            target=self.update_shared_memory_values,
            daemon=True
        )
        shared_memory_thread.start()


        washing_cycle_thread = threading.Thread(
            target=self.run_washing_cycle,
            daemon=True
        )
        washing_cycle_thread.start()



        # Keep threads running until stop is called
        while not self._stop_event.is_set():
            time.sleep(1)








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






class JobChecker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        
        # API configuration
        self.api_url = "http://srv630050.hstgr.cloud:3000/api/device/checkjobs"
        self.hub_id = "17348502838715973"
        self.device_id = 1000
        
        # Request configuration
        self.request_timeout = 10  # seconds
        self.check_interval = 5    # seconds between API checks
        
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
                device_status = float(response_data.get('devicestatus', 0))
                write_data_to_shared_memory("command_from_server", device_status)
                
            elif response.status_code == 204:
                # No job available
                write_data_to_shared_memory("command_from_server", 1000.0)
                
        except requests.exceptions.RequestException:
            # Handle request errors silently
            pass
        except ValueError:
            # Handle JSON parsing errors silently
            pass
        except Exception as e:
            print(f"Unexpected error in job checker: {e}")

    def stop(self):
        """Stop the job checker thread."""
        self._stop_event.set()

    def run(self):
        """Main thread execution loop."""
        try:
            while not self._stop_event.is_set():
                self.check_jobs()
                time.sleep(self.check_interval)
                
        except Exception as e:
            print(f"Error in job checker thread: {e}")
            self.stop()





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










class WashingMachineSystem:
    def __init__(self):
        # Initialize all components
        self.memory_manager = SharedMemoryManager()
        time.sleep(2)
        self.relay_controller = RelayController()
        self.washing_controller = WashingMachineController()
        self.sensor_reader = SensorReader()
        self.job_checker = JobChecker()
        self.tacho_sensor = TachoSensorThread()
        self.triac_controller = TriacController()
        
        # Store components for easier management
        self.components = [
            self.memory_manager,
            self.relay_controller,
            self.washing_controller,
            self.sensor_reader,
            self.job_checker,
            self.tacho_sensor,
            self.triac_controller
        ]
        
    def start_all(self):
        """Start all components in the correct order"""
        print("Starting washing machine system...")
        
        # Start components in order (memory manager first)
        self.memory_manager.start()
        print("Memory manager started")
        
        # Start all other components
        for component in self.components[1:]:
            component.start()
            component_name = component.__class__.__name__
            print(f"{component_name} started")
            
        print("All components started successfully")
        
    def stop_all(self):
        """Stop all components in reverse order"""
        print("\nStopping washing machine system...")
        
        # Stop all components in reverse order
        for component in reversed(self.components):
            try:
                component_name = component.__class__.__name__
                print(f"Stopping {component_name}...")
                component.stop()
                component.join()
                print(f"{component_name} stopped")
            except Exception as e:
                print(f"Error stopping {component_name}: {e}")
                
        # Special cleanup for specific components
        try:
            self.relay_controller.exit_handler()
            self.relay_controller.pi.stop()
        except Exception as e:
            print(f"Error in relay controller cleanup: {e}")
            
        try:
            write_data_to_shared_memory("relay_command", 14.0)
        except Exception as e:
            print(f"Error writing final relay command: {e}")
            
        print("System shutdown complete")

def main():
    # Create the system controller
    system = WashingMachineSystem()
    
    try:
        # Start all components
        system.start_all()
        
        # Keep main thread alive
        print("System running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutdown initiated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        # Clean shutdown of all components
        system.stop_all()

if __name__ == "__main__":
    main()
