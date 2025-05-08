import time
import threading
import requests
import json
from shared_memory_util import read_data_from_shared_memory, write_data_to_shared_memory


class WashingMachineControllerHeavy(threading.Thread):
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
        self.command_mode = 1000.0
        
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
                req_rpm_input -= 1.5
            elif (required_rpm - self.taccosensor) <= -10:
                req_rpm_input += 1.5
            else:
                break
            if(req_rpm_input>8000):
                req_rpm_input=6500
            if (req_rpm_input<4000):
                req_rpm_input=6500
            self.send_rpm(req_rpm_input)
            time.sleep(0.1)

    def stop_spin(self):
        write_data_to_shared_memory("relay_command", 5.0)
        time.sleep(5)
        self.send_rpm(7000)

    def stop_drain_spin(self):
        write_data_to_shared_memory("relay_command", 5.0)
        time.sleep(14)
        self.send_rpm(7000)

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
            self.check_and_load_water(11)

            self.set_al_direction()
            self.rpm_leveler(40)
            time.sleep(15)
            self.stop_spin()


    def drain_rotation_pattern_one(self):
        start_time = time.time()
        while (time.time() - start_time < 300):
            self.set_cl_direction()
            self.rpm_leveler(800)
            time.sleep(30)
            self.stop_drain_spin()
            self.drain_water(10)

            self.set_al_direction()
            self.rpm_leveler(800)
            time.sleep(30)
            self.stop_drain_spin()
            self.drain_water(10)

    def cycle_end(self):
        write_data_to_shared_memory("relay_command", 14.0)

    def run_washing_cycle(self):
        while not self._stop_event.is_set():
            try:
                #quick wash
                if self.command_mode == 0.0:
                    if self.command <= 0.0:
                        time.sleep(10)
                        self.close_door()
                        self.update_progress("05")
                        write_data_to_shared_memory("command_from_server", 5.0)
                    # elif self.command <= 4.0:
                    #     print("waiting for door to close")
                    #     waiting =1

                    elif self.command <= 5.0:
                        self.drain_water(5)
                        self.update_progress("10")
                        write_data_to_shared_memory("command_from_server", 10.0)

                    elif self.command <= 10.0:
                        self.check_and_load_water(11)
                        self.update_progress("15")
                        write_data_to_shared_memory("command_from_server", 15.0)

                    elif self.command <= 15.0:
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_one()
                        self.update_progress("20")
                        write_data_to_shared_memory("command_from_server", 20.0)

                    elif self.command <= 20.0:
                        self.drain_water(25)
                        self.update_progress("39")
                        write_data_to_shared_memory("command_from_server", 39.0)

                    elif self.command <= 39.0:
                        self.check_and_load_water(11)
                        self.update_progress("48")
                        write_data_to_shared_memory("command_from_server", 48.0)

                    elif self.command <= 48.0:
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_two()
                        self.update_progress("60")
                        write_data_to_shared_memory("command_from_server", 60.0)

                    elif self.command <= 60.0:
                        self.check_and_load_water(11)
                        self.update_progress("80")
                        write_data_to_shared_memory("command_from_server", 80.0)

                    elif self.command <= 80.0:
                        self.drain_water(50)
                        self.update_progress("85")
                        write_data_to_shared_memory("command_from_server", 85.0)

                    elif self.command <= 85.0:
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.update_progress("97")
                        write_data_to_shared_memory("command_from_server", 97.0)

                    elif self.command <= 97.0:
                        self.open_door()
                        self.update_ready()
                        write_data_to_shared_memory("command_from_server", 1000.0)
                        self.cycle_end()
                    time.sleep(1)

                #heavy wash
                elif self.command_mode == 0.0:
                    if self.command <= 0.0:
                        time.sleep(10)
                        self.close_door()
                        self.update_progress("05")
                        write_data_to_shared_memory("command_from_server", 5.0)

                    # elif self.command <= 4.0:
                    #     print("waiting for door to close")
                    #     waiting =1

                    elif self.command <= 5.0:
                        self.drain_water(5)
                        self.update_progress("10")
                        write_data_to_shared_memory("command_from_server", 10.0)

                    elif self.command <= 10.0:
                        self.check_and_load_water(11)
                        self.update_progress("15")
                        write_data_to_shared_memory("command_from_server", 15.0)

                    elif self.command <= 15.0:
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_one()
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_one()
                        self.update_progress("20")
                        write_data_to_shared_memory("command_from_server", 20.0)

                    elif self.command <= 20.0:
                        self.check_and_load_water(11)
                        self.drain_water(25)
                        self.update_progress("39")
                        write_data_to_shared_memory("command_from_server", 39.0)

                    elif self.command <= 39.0:
                        self.check_and_load_water(11)
                        self.update_progress("48")
                        write_data_to_shared_memory("command_from_server", 48.0)

                    elif self.command <= 48.0:
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_two()
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_two()
                        self.update_progress("60")
                        write_data_to_shared_memory("command_from_server", 60.0)

                    elif self.command <= 60.0:
                        self.check_and_load_water(11)
                        self.send_rpm(7000)
                        self.drum_rotation_pattern_two()
                        self.update_progress("80")
                        write_data_to_shared_memory("command_from_server", 80.0)

                    elif self.command <= 80.0:
                        self.drain_water(35)
                        self.update_progress("90")
                        write_data_to_shared_memory("command_from_server", 90.0)

                    elif self.command <= 90.0:
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.send_rpm(6500)
                        self.drain_rotation_pattern_one()
                        self.drain_water(10)
                        self.update_progress("97")
                        write_data_to_shared_memory("command_from_server", 97.0)

                    elif self.command <= 97.0:
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





def main():
    try:
        # Initialize and start washing machine controller
        controller = WashingMachineControllerHeavy()
        controller.start()

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    finally:
        # Clean shutdown
        controller.stop()
        controller.join()
        write_data_to_shared_memory("relay_command", 14.0)

if __name__ == "__main__":
    main()
