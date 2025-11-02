import time
from shared_memory_util import read_data_from_shared_memory

# Shared memory names
shared_memory_names = [
    "relay_command",
    "taccosensor",
    "doorssensor",
    "Pressure",
    "Water_Level",
    "Door_Status",
    "triac_delay",
    "command_from_server",
    "command_mode_from_server",  # For TRIAC delay
]




def monitor_shared_memory():
    while True:
        try:
            print("\nShared Memory Values:")
            for name in shared_memory_names:
                value = read_data_from_shared_memory(name)
                print(f"{name}: {value}")
            time.sleep(1)  # Adjust the delay as needed
        except KeyboardInterrupt:
            print("Monitoring stopped.")
            break

if __name__ == "__main__":
    monitor_shared_memory()
