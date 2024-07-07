import os
import time
import board
import busio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import globalsetting
from encoder import Encoder
from network import PiNetwork


class Functions:
    def __init__(self):
        self.network = PiNetwork()
        self.function_handlers = {
            "display_ip_local": self.display_ip_local,
            "display_ip_remote": self.display_ip_remote,
            "change_ip_local_dhcp": self.change_ip_local_dhcp,
            "change_ip_local_address": self.change_ip_local_address,
            "change_ip_remote_address": self.change_ip_remote_address,
            "change_code": self.change_code,
            "restart_network": self.restart_network,
            "restart_companion": self.restart_companion,
            "restart_raspberry": self.restart_raspberry,
        }

    def display_ip_local(self):
        try:
            return 'local: ' + self.network.get_current_ip()
        except Exception as e:
            return f"Error: {e}"

    def display_ip_remote(self):
        return 'remote: ' + '192.168.178.159'

    def change_ip_local_dhcp(self):
        print("Change Local IP to DHCP")

    def change_ip_local_address(self):
        print("Change Local IP Address")
        local_ip_menu = IpMenu(self.network.get_current_ip(), 'Local')
        global current_menu
        current_menu = local_ip_menu
        local_ip_menu.display()

    def change_ip_remote_address(self):
        print("Change Remote IP Address")

    def change_code(self):
        print("Change Code")

    def restart_network(self):
        print("Restart Network")

    def restart_companion(self):
        print("Restart Companion")

    def restart_raspberry(self):
        print("Restart Raspberry")


class IpMenu:
    def __init__(self, ip, instance):
        self.ip = str(ip)
        self.ip_segments = self.format_ip_segments(self.ip)
        self.instance = instance
        self.selected_index = 0
        self.edit_mode = False
        self.image = Image.new("1", (width, height), 0)
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

    def format_ip_segments(self, ip):
        segments = ip.split('.')
        formatted_segments = [segment.zfill(3) for segment in segments]
        return list('.'.join(formatted_segments))

    def get_ip_from_segments(self):
        return ''.join(self.ip_segments)

    def display(self):
        self.draw.rectangle((0, 0, width, height), outline=0, fill=0)
        self.draw.text((2, 0), "Peitsman - " + self.instance, font=self.font, fill=255)

        x_offset = 2
        ip_str = self.get_ip_from_segments()
        for i, char in enumerate(ip_str):
            char_width = 6

            if i == self.selected_index:
                if self.edit_mode:
                    self.draw.rectangle((x_offset - 1, 16, x_offset + char_width, 26), outline=255, fill=255)
                    self.draw.text((x_offset, 16), char, font=self.font, fill=0)
                else:
                    self.draw.rectangle((x_offset - 1, 16, x_offset + char_width, 26), outline=255, fill=0)
                    self.draw.text((x_offset, 16), char, font=self.font, fill=255)
            else:
                self.draw.text((x_offset, 16), char, font=self.font, fill=255)

            x_offset += char_width + 2  # Space between characters

        # Draw back button
        if len(ip_str) == self.selected_index:
            self.draw.rectangle((2, height - 20, 40, height - 2), outline=255, fill=255)
            self.draw.text((8, height - 18), "Back", font=self.font, fill=0)
        else:
            self.draw.rectangle((2, height - 20, 40, height - 2), outline=255, fill=0)
            self.draw.text((8, height - 18), "Back", font=self.font, fill=255)

        # Draw submit button
        if len(ip_str) + 1 == self.selected_index:
            self.draw.rectangle((width - 50, height - 20, width - 2, height - 2), outline=255, fill=255)
            self.draw.text((width - 45, height - 18), "Submit", font=self.font, fill=0)
        else:
            self.draw.rectangle((width - 50, height - 20, width - 2, height - 2), outline=255, fill=0)
            self.draw.text((width - 45, height - 18), "Submit", font=self.font, fill=255)

        oled.image(self.image)
        oled.show()
        
    def next_digit(self):
        while True:
            self.selected_index = ((self.selected_index + 1) % (len(self.ip_segments) + 2))
            if self.selected_index >= len(self.ip_segments) or self.ip_segments[self.selected_index] != '.':
                break
        self.display()

    def prev_digit(self):
        while True:
            self.selected_index = ((self.selected_index - 1) % (len(self.ip_segments) + 2))
            if self.selected_index >= len(self.ip_segments) or self.ip_segments[self.selected_index] != '.':
                break
        self.display()

    def increment_digit(self):
        if self.ip_segments[self.selected_index] != '.':
            current_value = int(self.ip_segments[self.selected_index])
            new_value = (current_value + 1) % 10
            self.ip_segments[self.selected_index] = str(new_value)

            # Adjust segment if necessary
            self.adjust_segment()

            self.display()

    def decrement_digit(self):
        if self.ip_segments[self.selected_index] != '.':
            current_value = int(self.ip_segments[self.selected_index])
            new_value = (current_value - 1) % 10
            if new_value < 0:
                new_value = 9
            self.ip_segments[self.selected_index] = str(new_value)

            # Adjust segment if necessary
            self.adjust_segment()

            self.display()

    def adjust_segment(self):
        segment_index = self.selected_index // 4  # Determine which IP segment we are editing
        ip_segments_str = self.get_ip_from_segments().split('.')
        current_segment = int(ip_segments_str[segment_index])
        
        # Make sure the segment is within the valid range
        if current_segment > 255:
            self.ip_segments[segment_index * 4] = '2'
            self.ip_segments[segment_index * 4 + 1] = '5'
            self.ip_segments[segment_index * 4 + 2] = '5'
        elif current_segment < 1:
            self.ip_segments[segment_index * 4] = '0'
            self.ip_segments[segment_index * 4 + 1] = '0'
            self.ip_segments[segment_index * 4 + 2] = '1'
        elif current_segment > 199 and self.ip_segments[segment_index * 4] == '2':
            if current_segment > 255:
                self.ip_segments[segment_index * 4 + 1] = '5'
                self.ip_segments[segment_index * 4 + 2] = '5'

    def select_item(self):
        if self.selected_index == len(self.ip_segments):
            # Back button selected
            self.back_button_pressed()
        elif self.selected_index == len(self.ip_segments) + 1:
            # Submit button selected
            self.submit_button_pressed()
        else:
            # Toggle edit mode for IP address segment
            self.edit_mode = not self.edit_mode
            self.display()

    def next_item(self):
        if self.edit_mode:
                self.increment_digit()
        else:
            self.next_digit()
    def prev_item(self):
        if self.edit_mode:
                self.decrement_digit()
        else:
            self.prev_digit()

    def back_button_pressed(self):
        # Handle back button press
        print("Back button pressed")
        # Example: Go back to previous screen or perform any other action

    def submit_button_pressed(self):
        # Handle submit button press
        print("Submit button pressed with IP:", self.get_ip_from_segments())
        # Example: Save changes or perform any other action



class MenuSystem:
    def __init__(self, menu_folder):
        global oled, image, draw, font
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
        global oled, image, draw, font
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
                        draw.text((2, 16 + (i - start_idx) * 16), functions.function_handlers[menu[i][2]](), font=font, fill=0)
                    else:
                        draw.text((2, 16 + (i - start_idx) * 16), menu[i][0], font=font, fill=0)
                else:
                    if menu[i][1] == '997':
                        draw.text((2, 16 + (i - start_idx) * 16), functions.function_handlers[menu[i][2]](), font=font, fill=255)
                    else:
                        draw.text((2, 16 + (i - start_idx) * 16), menu[i][0], font=font, fill=255)

        oled.image(image)
        oled.show() 

    def select_item(self):
        self.selected_index += 1

        item = self.menu_data[self.current_screen][self.selected_index]
        flag = int(item[1])
        if flag == 999 or flag == 997:
            self.selected_index -= 1
            self.display_menu()
            return  # informational, do nothing
        elif flag == 998:
            functions.function_handlers[item[2]]()

            return
        else:
            self.current_screen = flag

        self.last_interaction_time = time.time()
        self.scroll_offset = 0  # Reset scroll offset after menu change
        self.selected_index = 0
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
        global oled, image, draw, font
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        draw.text((2, height // 2 - 8), "Screen Locked", font=font, fill=255)
        oled.image(image)
        oled.show()
        while True:
            time.sleep(1)


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

# Instantiate function handlers and menu system
functions = Functions()
menu_system = MenuSystem(globalsetting.MENU_FOLDER)

# Display initial menu
menu_system.display_menu()

current_menu = menu_system

# Button handling
def button_select_pressed():
    current_menu.select_item()

def rotary_encoder(value, direction):
    if direction == "R":
        current_menu.next_item()
    elif direction == "L":
        current_menu.prev_item()

# Initialize encoder
encoder = Encoder(6, 13, 5, rotary_encoder, button_select_pressed)

# Main loop
try:
    while True:
        menu_system.check_lock_screen()
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()