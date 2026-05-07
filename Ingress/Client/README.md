# OPC UA Client – Laser Control Interface

## Purpose
This client connects to the OPC UA Laser Control Server to send commands, retrieve status updates, and subscribe to live data changes from the server. It serves as the bridge between a Python application and the laser machine, providing high-level control methods.

This client acts as the main link between user applications (e.g., GUI) and the backend OPC UA server, enabling:
* Connection management
* Live data subscriptions** for status variables
* Laser hardware control commands
* File management for G-code programs

---

## Structure

### 1. **Initialization**
* Takes an OPC UA server URL (default: `opc.tcp://0.0.0.0:4840/laser/`).
* Creates a `Client` instance from `asyncua.sync`.
* Defines internal state variables for connection, subscriptions, and monitored nodes.
* Automatically attempts connection during instantiation.

### 2. **Connection Handling**
* `connect()`: Establishes connection, retrieves namespace index, and initializes OPC UA nodes.
* `exit()`: Disconnects the client, stops the event loop, and cleans up subscriptions.

### 3. **Subscriptions**
* Monitors key status nodes:
  * `is_connected`
  * `is_mcu_connected`
  * `is_running`
  * `progress`
  * `list_of_files`
* `datachange_notification()`: Callback triggered when monitored node values change.

### 4. **Control Methods**
* Machine control: `reference()`, `stop()`, `pointer()`, `fan_control()`.
* Motion control: `move_actuator_hight()`, `move_actuator_push()`, `move_relativ()`, `move_absolut()`.
* Card handling: `push_card_in()`, `push_card_out()`.

### 5. **G-code Operations**
* File management: `list_files()`, `get_gcode()`, `run_file()`.
* On-the-fly generation and execution: `generate_gcode()`, `get_generated_gcode()`, `run_generated_gcode()`.

### 6. **Status Queries**
* Connection checks: `is_connected()`, `is_laser_connected()`, `is_mcu_connected()`.
* Progress and job state: `get_progress()`, `is_running()`.

---

## Dependencies

Install required libraries:

```bash
pip install asyncua
```

> `asyncua` includes both sync and async OPC UA capabilities.

---

## Example Usage

```python
from laser_client import Laser  # This file
import time

# Create a client instance
laser = Laser("opc.tcp://192.168.157.213:4840/laser/")

# Check connection
if laser.is_connected():
    print("Connected to server.")
    print("Laser connected:", laser.is_laser_connected())
    print("MCU connected:", laser.is_mcu_connected())

    # Move laser head
    laser.move_absolut(100, 50, 5000)

    # Run a G-code file
    laser.run_file("test_file.gcode")

    # Monitor progress
    while laser.is_running():
        print("Progress:", laser.get_progress() * 100, "%")
        time.sleep(1)

    print("Job finished.")
else:
    print("Failed to connect to server.")

# Disconnect cleanly
laser.exit()
```
