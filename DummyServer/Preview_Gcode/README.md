# GCodePreview

## Overview
`GCodePreview` is a Python class for visualizing G-code instructions by generating a graphical preview.  
It uses the Python Imaging Library (PIL) to draw lines representing laser engraving tool paths.

## Features
- Parses G-code commands (`G0`, `G1`, `M3`, `M4`, `M5`, etc.).
- Supports both absolute (`G90`) and relative (`G91`) positioning.
- Generates a scaled preview image of the engraving.
- Allows customization of:
  - Card width and height (in mm)
  - Scaling factor for rendering
  - Background and foreground colors
  - Line width
  - Offset for coordinate adjustment

## Methods
- **`parse_gcode(draw, gcode)`**  
  Reads G-code line-by-line, processes motion and laser power commands, and draws paths on an image.

- **`generate_preview(gcode_data)`**  
  Creates and returns a PIL image preview of the provided G-code.

- **`set_offset(x, y)`**  
  Adjusts the offset applied to the parsed G-code coordinates.

## Dependencies
- Python 3.x
- `Pillow` library (`pip install pillow`)
- `re` (standard library)

## Example Usage
```python
from GCodePreview import GCodePreview

preview = GCodePreview(scale_factor=10, line_width=2)
with open("example.gcode", "r") as f:
    gcode_data = f.read()

image = preview.generate_preview(gcode_data)
image.show()
```
