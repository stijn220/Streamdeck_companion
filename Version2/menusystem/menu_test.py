import time
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import busio

# Create the I2C interface
i2c = busio.I2C(board.SCL, board.SDA)

# Create the display object
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Clear display.
oled.fill(0)
oled.show()

# Create blank image for drawing.
width = oled.width
height = oled.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Load default font.
font = ImageFont.load_default()

# Menu items
menu_items = ["Item 1", "Item 2", "Item 3", "Item 4"]
selected_index = 0

def draw_menu(selected_index):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)  # Clear the screen
    for i, item in enumerate(menu_items):
        if i == selected_index:
            draw.rectangle((0, i * 16, width, (i + 1) * 16), outline=255, fill=255)
            draw.text((2, i * 16), item, font=font, fill=0)
        else:
            draw.text((2, i * 16), item, font=font, fill=255)
    oled.image(image)
    oled.show()

# Draw the initial menu
draw_menu(selected_index)

while True:
    # Here you would normally use input methods to update `selected_index`
    # For the purpose of this example, we'll simulate this with a sleep loop
    time.sleep(1)
    selected_index = (selected_index + 1) % len(menu_items)
    draw_menu(selected_index)
