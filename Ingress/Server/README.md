# OPC UA Laser Control Server

This server provides an **OPC UA interface** for controlling a laser engraver, managing G-code, and handling engraving orders.  
It exposes methods to move actuators, send laser commands, preview and run G-code, and track order progress.

## Purpose
The server acts as a bridge between clients (such as the provided GUI) and the hardware control logic.  
It enables:
- Remote control of the laser engraver (file execution, G-code commands, actuator movement).
- Live monitoring of system state (connection status, progress, available files).
- G-code generation for engraving tasks.
- Basic order queue operations *(note: order handling backend is not fully implemented)*.

## Structure
1. **Server Setup**
   - Runs on `opc.tcp://0.0.0.0:4840/laser/`.
   - Uses the `asyncua` library to provide asynchronous OPC UA communication.
   - Namespace: `laser_module`.

2. **Main Objects**
   - `status` → Flags for connection state, MCU link, running status, progress.
   - `gcode` → Methods for generating, loading, and running G-code.
   - `control` → General commands (connect, stop, fan control, pointer).
   - `move` → Positioning commands and actuator control.
   - `orders` → Order queue variables and methods *(stub)*.

3. **Exposed Methods**
   - **Laser control**: `reference`, `run_file`, `run_code`, `stop`, `pointer`, `fan_control`.
   - **G-code generation**: `generate_gcode`, `get_generated_gcode`, `run_generated_gcode`.
   - **Position control**: `move_relativ`, `move_absolut`, `move_actuator_hight`, `move_actuator_push`.
   - **Order operations** *(stub)*: `add_new_order`, `mark_done`, `get_order_status`.
   - **Hardware actions**: `connect`, `push_card_in`, `push_card_out`.

4. **Variable Updates**
   - Continuously updates OPC UA variables with current machine state and order queue statistics.

---

## Dependencies

Install required packages with:

```bash
pip install asyncua
```

You also need the project’s internal modules:
- `Laser_Control.laser`
- `Generate_Gcode.Generate_Gcode`
- `orders`

---

## How It Works

The server:
1. Starts an **OPC UA endpoint** at:
   ```
   opc.tcp://0.0.0.0:4840/laser/
   ```
2. Registers objects:
   - **status** – live connection and progress info
   - **gcode** – for handling G-code files and commands
   - **control** – laser operation methods
   - **move** – actuator and motion commands
   - **orders** – manage engraving job queue
3. Updates all variable values in a loop (connection state, progress, file list, order queue).

---

## Example Usage

### 1. Start the server
```bash
python opcua_server.py
```

### 2. Connect to the server
Using Python’s `asyncua` client:

```python
import asyncio
from asyncua import Client

async def main():
    url = "opc.tcp://localhost:4840/laser/"
    async with Client(url=url) as client:
        # Call a method (example: reference laser)
        result = await client.nodes.objects.call_method("ns=2;s=reference")
        print("Reference result:", result)

        # Get variable value (example: laser progress)
        progress_node = await client.nodes.objects.get_child("2:status/2:progress")
        progress_value = await progress_node.read_value()
        print("Laser progress:", progress_value)

asyncio.run(main())
```

---

## Notes
- This server expects a **laser engraver** and related hardware connected, unless you run it with:
  ```python
  laser = Laser(dummy=True)
  ```
  which simulates the device.
- **Order handling** is partially implemented; methods exist, but the order processing logic must be completed in `orders.py`.
