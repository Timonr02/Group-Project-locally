# Laser Engraver GUI

## Purpose

The **LaserGUI** provides a graphical interface for controlling the laser engraving system, monitoring machine status, previewing G-code, and coordinating with a UR5 robot for material handling.

---

## Key Features

* **Machine Control**
  * Connect/disconnect from the OPC UA server
  * Enable/disable laser pointer and exhaust fan
  * Servo actuator height and push control
  * Relative and absolute movement of the laser head
  * Referencing (homing) support

* **G-code Operations**
  * Load and run stored G-code files
  * Generate new G-code from templates and user input
  * Preview generated G-code before running

* **Status Monitoring**
  * Live OPC UA connection status
  * Laser, MCU, and job running status
  * Real-time progress bar and percentage display
  * Available program list with refresh

* **UR5 Robot Integration**

  * Pick/place cards from specific modules
  * Request card supply or removal

* **Origin Selection**
  * Set engraving origin to "Front" or "Back"
  * Automatically adjusts G-code offsets for the preview and laser

---

## Dependencies

Install required packages:

```bash
pip install asyncua pillow
```

Tkinter is part of Python’s standard library.

---

## Example Usage

```bash
python laser_gui.py
```

The GUI will launch in full-screen mode, displaying:

* A control tab for movement and job execution
* A G-code generation tab for creating new engraving designs
* An NFC tab (placeholder for future expansion)
