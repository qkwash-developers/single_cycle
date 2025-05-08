import pigpio
import time
import threading
from shared_memory_util import create_shared_memory, read_data_from_shared_memory, write_data_to_shared_memory

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
        time.sleep(0.12)
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
        write_data_to_shared_memory("command_mode_from_server", 1000.0)


    def stop(self):
        """Stop the thread."""
        self._stop_event.set()

    def run(self):
        """Main thread loop."""
        self.initialize_shared_memory()
        while not self._stop_event.is_set():
            # Add any periodic shared memory operations here
            time.sleep(1)

def main():
    try:
        # Initialize and start shared memory manager
        memory_manager = SharedMemoryManager()
        memory_manager.start()

        # Initialize and start relay controller
        relay_controller = RelayController()
        relay_controller.start()

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    finally:
        # Clean shutdown
        memory_manager.stop()
        relay_controller.stop()
        memory_manager.join()
        relay_controller.join()
        relay_controller.exit_handler()
        relay_controller.pi.stop()

if __name__ == "__main__":
    main()