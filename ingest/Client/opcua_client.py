from asyncio import sleep
from asyncua.sync import Client

# URL = "opc.tcp://192.168.157.213:4840/laser/"
URL = "opc.tcp://0.0.0.0:4840/laser/"

class Laser:

    def __init__(self, url = URL):
        self.client = Client(url, 50)

        self.namespace = "laser_module"
        self._is_connected = False
        self._is_referenced = False

        self.subscription = None
        self.handles = []
        self.connected = False

        self.nodes_to_monitor = {}
        self.current_values = {}

        self.connect()

    def connect(self):
        if self._is_connected:
            self.control.call_method(f"{self.nsidx}:connect")
        else:
            try:
                self.client.connect()

                self.nsidx = self.client.get_namespace_index(self.namespace)
                self.status = self.client.nodes.root.get_child(
                    ["0:Objects", f"{self.nsidx}:status"]
                )
                self.gcode = self.client.nodes.root.get_child(
                    ["0:Objects", f"{self.nsidx}:gcode"]
                )
                self.control = self.client.nodes.root.get_child(
                    ["0:Objects", f"{self.nsidx}:control"]
                )
                self.move = self.client.nodes.root.get_child(
                    ["0:Objects", f"{self.nsidx}:move"]
                )
                self.nodes_to_monitor = {
                    "is_connected": self.status.get_child(f"{self.nsidx}:is_connected"),
                    "is_mcu_connected": self.status.get_child(f"{self.nsidx}:is_mcu_connected"),
                    "is_running": self.status.get_child(f"{self.nsidx}:is_running"),
                    "progress": self.status.get_child(f"{self.nsidx}:progress"),
                    "last_job_duration_s": self.status.get_child(f"{self.nsidx}:last_job_duration_s"),
                    "count_finished_card": self.status.get_child(f"{self.nsidx}:count_finished_card"),
                    "list_of_files": self.gcode.get_child(f"{self.nsidx}:list_of_files"),
                }

                self.start_subscription()
                self._is_connected = True
            except:
                pass

    def exit(self):
        try:
            if self._is_connected:
                self.client.disconnect()
            self.client.tloop.stop()
            self.stop_subscription()
        except:
            pass

    def start_subscription(self):
        self.current_values = {key: None for key in self.nodes_to_monitor.keys()}

        self.subscription = self.client.create_subscription(100, self)
        for _, node in self.nodes_to_monitor.items():
            handle = self.subscription.subscribe_data_change(node)
            self.handles.append(handle)

    def stop_subscription(self):
        if self.subscription:
            # self.subscription.unsubscribe(self.handles)
            for self.handle in self.handles.values():
                self.subscription.unsubscribe(self.handle)
            self.handles = {}
            self.subscription.delete() 
            self.subscription = None

    def datachange_notification(self, node, val, _):
        for key, monitored_node in self.nodes_to_monitor.items():
            if monitored_node == node:
                self.current_values[key] = val
                print(f"DataChange {key}: {val}")

    def reference(self):
        if self._is_connected:
            return self.control.call_method(f"{self.nsidx}:reference")
        return False

    def move_actuator_hight(self, angle: int = 0) -> int:
        if self._is_connected:
            return self.move.call_method(f"{self.nsidx}:move_actuator_hight", angle)
        return False

    def move_actuator_push(self, angle: int = 0) -> int:
        if self._is_connected:
            return self.move.call_method(f"{self.nsidx}:move_actuator_push", angle)
        return False

    def move_relativ(self, xval: int = 0, yval: int = 0) -> int:
        if self._is_connected:
            return self.move.call_method(f"{self.nsidx}:move_relativ", xval, yval)
        return False

    def move_absolut(self, xval: int = 0, yval: int = 0, feed: int = 10000) -> int:
        if self._is_connected:
            return self.move.call_method(f"{self.nsidx}:move_absolut", xval, yval, feed)
        return False

    def push_card_in(self):
        if not self._is_connected:
            return
        return self.move.call_method(f"{self.nsidx}:push_card_in")

    def push_card_out(self):
        if not self._is_connected:
            return
        return self.move.call_method(f"{self.nsidx}:push_card_out")

    def list_files(self) -> list[str]:
        if not self._is_connected:
            return []
        return self.current_values["list_of_files"]

    def generate_gcode(
        self, variant, title, name, division, job_title, phone, fax, mail
    ):
        if self._is_connected:
            self.gcode.call_method(
                f"{self.nsidx}:generate_gcode",
                variant,
                title,
                name,
                division,
                job_title,
                phone,
                fax,
                mail,
            )

    def get_generated_gcode(self) -> str:
        if self._is_connected:
            return self.gcode.call_method(f"{self.nsidx}:get_generated_gcode")
        return ""

    def run_generated_gcode(self) -> str:
        if self._is_connected:
            return self.gcode.call_method(f"{self.nsidx}:run_generated_gcode")
        return -1

    def run_file(self, filename: str):
        if self._is_connected:
            return self.gcode.call_method(f"{self.nsidx}:run_file", filename)
        return -1

    def get_gcode(self, filename: str) -> str:
        if self._is_connected:
            return self.gcode.call_method(f"{self.nsidx}:get_gcode", filename)
        return ""


    def stop(self):
        if self._is_connected:
            self.control.call_method(f"{self.nsidx}:stop")

    def send_command(self, command):
        if self._is_connected:
            return self.control.call_method(f"{self.nsidx}:send_command", command)
        return -1

    def set_card_offset(self,x: int, y: int):
        if not self._is_connected:
            return
        self.control.call_method(f"{self.nsidx}:set_card_offset", x,y)

    def is_connected(self):
        return self._is_connected

    def is_laser_connected(self):
        if not self._is_connected:
            return False
        return self.current_values["is_connected"]

    def is_mcu_connected(self):
        if not self._is_connected:
            return False
        return self.current_values["is_mcu_connected"]

    def get_progress(self):
        if not self._is_connected:
            return False
        return self.current_values["progress"]/100

    def get_last_job_duration_s(self):
        if not self._is_connected:
            return False
        return self.current_values["last_job_duration_s"]

    def is_running(self):
        if not self._is_connected:
            return False
        return self.current_values["is_running"]

    def pointer(self, on: bool):
        if not self._is_connected:
            return False
        self.control.call_method(f"{self.nsidx}:pointer", on)
        return 0

    def fan_control(self, on: bool):
        if not self._is_connected:
            return False
        self.control.call_method(f"{self.nsidx}:fan_control", on)
        return 0


if __name__ == "__main__":
    laser = Laser()
    print(laser.list_files())
    print(laser.generate_gcode("hs","","","","","","",""))
    print(laser.get_generated_gcode())

