import os
import time
import board
import busio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import globalsetting
from myFunctions import functionHandlersDictionary
from encoder import Encoder


# Initialize OLED display
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Clear display
oled.fill(0)
oled.show()

# Create image for drawing
width = oled.width
height = oled.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# Load font
font = ImageFont.load_default()

# Menu system
class MenuSystem:
    def __init__(self, menu_folder):
        self.menu_folder = menu_folder
        self.current_screen = 0
        self.menu_data = self.load_menus()
        self.selected_index = 0
        self.last_interaction_time = time.time()
        self.locked = False
        self.scroll_offset = 0
        self.visible_items = 3

    def load_menus(self):
        menus = {}
        try:
            for filename in sorted(os.listdir(self.menu_folder)):
                if filename.startswith('menu.'):
                    screen_num = int(filename.split('.')[1])
                    with open(os.path.join(self.menu_folder, filename), 'r') as f:
                        menu_lines = f.readlines()
                        menu_name = "Peitsman - " + menu_lines[0].strip()  # Read menu name from first line
                        menus[screen_num] = [line.strip().split(',') for line in menu_lines[1:]]  # Exclude first line
                        menus[screen_num].insert(0, [menu_name, "999"])  # Insert menu title as first item
        except FileNotFoundError as e:
            print(f"Error: {e}")
            raise
        return menus

    def display_menu(self):
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        
        # Draw menu title
        draw.text((2, 0), self.menu_data[self.current_screen][0][0], font=font, fill=255)
        
        menu = self.menu_data[self.current_screen][1:]  # Exclude the title from menu items
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_items, len(menu))
        
        for i in range(start_idx, end_idx):
            if start_idx <= self.selected_index < end_idx:
                if i == self.selected_index:
                    draw.rectangle((0, 16 + (i - start_idx) * 16, width, 16 + (i - start_idx + 1) * 16), outline=255, fill=255)
                    if menu[i][1] == '997':
                        draw.text((2, 16 + (i - start_idx) * 16), functionHandlersDictionary[menu[i][2]](), font=font, fill=0)
                    else:
                        draw.text((2, 16 + (i - start_idx) * 16), menu[i][0], font=font, fill=0)
                else:
                    if menu[i][1] == '997':
                        draw.text((2, 16 + (i - start_idx) * 16), functionHandlersDictionary[menu[i][2]](), font=font, fill=255)
                    else: 
                        draw.text((2, 16 + (i - start_idx) * 16), menu[i][0], font=font, fill=255)
        
        oled.image(image)
        oled.show()


    def select_item(self):
        self.selected_index += 1

        item = self.menu_data[self.current_screen][self.selected_index]
        flag = int(item[1])
        if flag == 999 or flag == 997:
            return  # informational, do nothing
        elif flag == 998:
            functionHandlersDictionary[item[2]]()
        else:
            self.current_screen = flag
        self.selected_index = 0
        self.last_interaction_time = time.time()
        self.scroll_offset = 0  # Reset scroll offset after menu change
        self.display_menu()  # Refresh the menu display after selection



    def next_item(self):
        if self.selected_index < len(self.menu_data[self.current_screen]) - 2:
            self.selected_index += 1
            if self.selected_index >= self.scroll_offset + self.visible_items:
                self.scroll_offset += 1
        else:
            self.selected_index = 0
            self.scroll_offset = 0
        self.last_interaction_time = time.time()
        self.display_menu()

    def prev_item(self):
        if self.selected_index > 0:
            self.selected_index -= 1
            if self.selected_index < self.scroll_offset:
                self.scroll_offset -= 1
        else:
            self.selected_index = len(self.menu_data[self.current_screen]) - 2
            self.scroll_offset = max(0, len(self.menu_data[self.current_screen]) - self.visible_items - 1)
        self.last_interaction_time = time.time()
        self.display_menu()

    def check_lock_screen(self):
        if time.time() - self.last_interaction_time > globalsetting.SCREEN_LOCK_TIMEOUT:
            self.lock_screen()

    def lock_screen(self):
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw.text((2, height // 2 - 8), "Screen Locked", font=font, fill=255)
        oled.image(image)
        oled.show()
        while True:
            time.sleep(1)

menu_system = MenuSystem(globalsetting.MENU_FOLDER)

# Display initial menu
menu_system.display_menu()

# Button handling
def button_select_pressed():
    menu_system.select_item()

def rotary_encoder(value, direction):
    if direction == "R":
        menu_system.next_item()
    elif direction == "L":
        menu_system.prev_item()


encoder = Encoder(6, 13, 5, rotary_encoder, button_select_pressed)


try:
    while True:
        menu_system.check_lock_screen()
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
