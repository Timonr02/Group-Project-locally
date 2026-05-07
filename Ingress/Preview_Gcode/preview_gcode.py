import re
from PIL import Image, ImageDraw


class GCodePreview:
    def __init__(
        self,
        card_width=85,
        card_height=54,
        scale_factor=8,
        background_color="#FFFFFF",
        forground_color="#000000",
        offset=[4, 86],
        line_width = 1,
    ):
        self.card_width = card_width
        self.card_height = card_height
        self.scale_factor = scale_factor
        self.background_color = background_color
        self.forground_color = forground_color
        self.line_width = line_width
        self.offset = offset

        self.img_width = int(self.card_width * self.scale_factor)
        self.img_height = int(self.card_height * self.scale_factor)

    def parse_gcode(self, draw, gcode):
        lines = gcode.strip().split("\n")
        current_position = [0, 0]
        abs_mode = True
        power_on = False
        x = 0
        y = 0
        s_value = 0

        for line in lines:
            line = line.replace(
                "X" + str(self.offset[0]) + "Y" + str(self.offset[1]) + "F5000S0",
                "X0Y00F5000S0",
            )
            if line.startswith((";", "$H")) or not line.strip():
                continue

            if line.startswith("G90"):
                abs_mode = True
            elif line.startswith("G91"):
                abs_mode = False
            elif line.startswith("M3") or line.startswith("M4"):
                power_on = True
            elif line.startswith("M5"):
                power_on = False

            if line.startswith(("G0", "G00", "G1", "G01", "M3")):
                matches = re.findall(
                    r"X([-+]?[0-9]*\.?[0-9]+)|Y([-+]?[0-9]*\.?[0-9]+)|S([0-9]+)", line
                )
                for match in matches:
                    if match[0]:
                        x_new = float(match[0]) * self.scale_factor
                        x = x_new if abs_mode else x + x_new
                    if match[1]:
                        y_new = float(match[1]) * self.scale_factor
                        y = y_new if abs_mode else y + y_new
                    if match[2]:
                        s_value = int(match[2])
                    # else:
                    #     s_value = 0

                new_position = [x, y]
                if line.startswith(("G0", "G00")):
                    pass
                elif power_on and (s_value > 0):
                    draw.line(
                        [tuple(current_position), tuple(new_position)],
                        fill=self.forground_color,
                        width=self.line_width,
                    )
                current_position = new_position

    def generate_preview(self, gcode_data):
        image = Image.new(
            "RGB", (self.img_width, self.img_height), self.background_color
        )
        draw = ImageDraw.Draw(image)
        self.parse_gcode(draw, gcode_data)
        image = image.transpose(method=Image.FLIP_TOP_BOTTOM)
        # image.show()
        return image

    def set_offset(self, x, y):
        self.offset = [x, y]


if __name__ == "__main__":
    file_path = "test_Generate.gc"
    with open(file_path, "r") as file:
        gcode_data = file.read()
    prev = GCodePreview(background_color="#000000", forground_color="#FFFFFF", line_width=1)
    img = prev.generate_preview(gcode_data)
    print("Image generated")
    img.show()
    print("Image shown")

