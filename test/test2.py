import digitalio
import board
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import pygame
import pygame.freetype
from encoder import Encoder  # Import Encoder class from your encoder module

class Menu:
    def __init__(self):
        # Screen Variables
        self.width = 128
        self.height = 64
        self.reset_pin = digitalio.DigitalInOut(board.D4)
        self.i2c = None
        self.oled = None
        self.image = None
        self.draw = None
        self.font = None
        self.initialize_display()

        # Constants for screen dimensions
        self.SCREEN_WIDTH = self.width
        self.SCREEN_HEIGHT = self.height

        # Colors
        self.BLACK = 0
        self.WHITE = 255

        # Font settings
        self.FONT_SIZE = 16
        self.FONT = ImageFont.load_default()

        # Mock settings data
        self.settings = {
            "Layer 1": ["Option 1", "Option 2", "Option 3"],
            "Layer 2": ["Option A", "Option B", "Option C"],
            "Layer 3": ["Option X", "Option Y", "Option Z"]
        }

        # Main loop variables
        self.running = True
        self.layer_index = 0
        self.selected_option_index = 0

        # Rotary encoder
        self.encoder = Encoder(6, 13, 5, self.update)

    def initialize_display(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, self.i2c, addr=0x3C, reset=self.reset_pin)
        self.image = Image.new("1", (self.oled.width, self.oled.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

    def draw_text(self, text, x, y, font, color):
        self.draw.text((x, y), text, font=font, fill=color)

    def render(self):
        self.oled.fill(0)
        current_layer = list(self.settings.keys())[self.layer_index]
        options = self.settings[current_layer]

        # Draw options
        for i, option in enumerate(options):
            y = 10 + i * self.FONT_SIZE
            if i == self.selected_option_index:
                # Highlight the selected option (e.g., change color or font weight)
                self.draw_text(option, 10, y, self.FONT, self.WHITE)
            else:
                self.draw_text(option, 10, y, self.FONT, self.WHITE)

        self.oled.image(self.image)
        self.oled.show()

    def update(self, value, direction):
        if direction == "R":
            self.selected_option_index = (self.selected_option_index + 1) % len(self.settings[list(self.settings.keys())[self.layer_index]])
        elif direction == "L":
            self.selected_option_index = (self.selected_option_index - 1) % len(self.settings[list(self.settings.keys())[self.layer_index]])
        self.render()

    def run(self):
        while self.running:
            # Handle other events here if needed
            pass


if __name__ == "__main__":
    menu = Menu()
    menu.run()
