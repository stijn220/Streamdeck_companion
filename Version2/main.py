import os
import time
import board
import busio
import json
import subprocess
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import globalsetting
from encoder import Encoder
from network import PiNetwork


class Satellite:
    def __init__(self):
        self.satellite_folder = globalsetting.SATELLITE_FOLDER
        self.satellite_config = globalsetting.SATELLITE_CONFIG
        self.start_service()

    def get_remote_ip(self):
        try:
            with open(self.satellite_config) as f:
                config_data = json.load(f)
                return config_data.get("remoteIp")
        except FileNotFoundError:
            print(f"File {self.satellite_config} not found.")
        except PermissionError:
            print(f"Permission denied: Unable to access {self.satellite_config}.")
            return "Error"
        except Exception as e:
            print(f"An error occurred: {e}")

    def change_remote_ip(self, new_ip):
        try:
            with open(self.satellite_folder, 'r') as config_file:
                lines = config_file.readlines()

            with open(self.satellite_folder, 'w') as config_file:
                for line in lines:
                    if line.startswith("# COMPANION_IP="):
                        print(line)
                        config_file.write(f"COMPANION_IP={new_ip}\n")
                        print(f"COMPANION_IP={new_ip}\n")
                    else:
                        config_file.write(line)
            print(f"COMPANION_IP changed to {new_ip}")
            self.restart_service()
        except FileNotFoundError:
            print(f"File {self.satellite_folder} not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def start_service(self):
        try:
            subprocess.run(["sudo", "systemctl", "start", "satellite"])
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error rebooting: {e}")

    def restart_service(self):
        try:
            subprocess.run(["sudo", "systemctl", "restart", "satellite"])
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error rebooting: {e}")


class Functions:
    def __init__(self):
        self.network = PiNetwork()
        self.satellite = Satellite()
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
            return "local: " + self.network.get_current_ip()
        except Exception as e:
            return f"Error: {e}"

    def display_ip_remote(self):
        return "remote: " + self.satellite.get_remote_ip()

    def change_ip_local_dhcp(self):
        print("Change Local IP to DHCP")

    def change_ip_local_address(self):
        local_ip_menu = IpMenu(self.network.get_current_ip(), "Local", self.submit_ip_local_address)
        global current_menu
        current_menu = local_ip_menu
        local_ip_menu.display()

    def change_ip_remote_address(self):
        remote_ip_menu = IpMenu(self.satellite.get_remote_ip(), "Remote", self.submit_ip_remote_address)
        global current_menu
        current_menu = remote_ip_menu
        remote_ip_menu.display()

    def submit_ip_local_address(self, ip):
        self.local_ip = ip
        self.network.set_static_ip(self.local_ip)
    
    def submit_ip_remote_address(self, ip):
        self.remote_ip = ip
        self.satellite.change_remote_ip(self.remote_ip)
    
    def change_code(self):
        print("Change Code")

    def restart_network(self):
        print("Restart Network")

    def restart_companion(self):
        print("Restart Companion")

    def restart_raspberry(self):
        print("Restart Raspberry")


class IpMenu:
    def __init__(self, ip, instance, callback):
        self.ip = str(ip)
        self.ip_segments = self.format_ip_segments(self.ip)
        self.instance = instance
        self.callback = callback
        self.selected_index = 0
        self.edit_mode = False
        self.image = Image.new("1", (width, height), 0)
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

    def format_ip_segments(self, ip):
        segments = ip.split(".")
        formatted_segments = [segment.zfill(3) for segment in segments]
        return list(".".join(formatted_segments))

    def get_ip_from_segments(self):
        return "".join(self.ip_segments)

    def is_valid_ip(self, ip):
        segments = ip.split(".")
        if len(segments) != 4:
            return False
        for i, segment in enumerate(segments):
            if not segment.isdigit():
                return False

            cleaned_segment = str(int(segment))  # This removes leading zeros
            if not (0 <= int(cleaned_segment) <= 255):
                return False
            segments[i] = cleaned_segment

        return True

    def display(self):
        self.draw.rectangle((0, 0, width, height), outline=0, fill=0)
        self.draw.text((2, 0), "Peitsman - " + self.instance, font=self.font, fill=255)

        x_offset = 2
        ip_str = self.get_ip_from_segments()
        for i, char in enumerate(ip_str):
            char_width = 6

            if i == self.selected_index:
                if self.edit_mode:
                    self.draw.rectangle(
                        (x_offset - 1, 16, x_offset + char_width, 26), outline=255, fill=255, )
                    self.draw.text((x_offset, 16), char, font=self.font, fill=0)
                else:
                    self.draw.rectangle(
                        (x_offset - 1, 16, x_offset + char_width, 26), outline=255, fill=0, )
                    self.draw.text((x_offset, 16), char, font=self.font, fill=255)
            else:
                self.draw.text((x_offset, 16), char, font=self.font, fill=255)

            x_offset += char_width + 2

        if len(ip_str) == self.selected_index:
            self.draw.rectangle((2, height - 20, 40, height - 2), outline=255, fill=255)
            self.draw.text((8, height - 18), "Back", font=self.font, fill=0)
        else:
            self.draw.rectangle((2, height - 20, 40, height - 2), outline=255, fill=0)
            self.draw.text((8, height - 18), "Back", font=self.font, fill=255)

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
            self.selected_index = (self.selected_index + 1) % (
                len(self.ip_segments) + 2
            )
            if (
                self.selected_index >= len(self.ip_segments)
                or self.ip_segments[self.selected_index] != "."
            ):
                break
        self.display()

    def prev_digit(self):
        while True:
            self.selected_index = (self.selected_index - 1) % (
                len(self.ip_segments) + 2
            )
            if (
                self.selected_index >= len(self.ip_segments)
                or self.ip_segments[self.selected_index] != "."
            ):
                break
        self.display()

    def increment_digit(self):
        if self.ip_segments[self.selected_index] != ".":
            current_value = int(self.ip_segments[self.selected_index])
            new_value = (current_value + 1) % 10
            self.ip_segments[self.selected_index] = str(new_value)

            self.adjust_segment()

            self.display()

    def decrement_digit(self):
        if self.ip_segments[self.selected_index] != ".":
            current_value = int(self.ip_segments[self.selected_index])
            new_value = (current_value - 1) % 10
            if new_value < 0:
                new_value = 9
            self.ip_segments[self.selected_index] = str(new_value)
            self.adjust_segment()
            self.display()

    def adjust_segment(self):
        segment_index = (
            self.selected_index // 4
        )  # Determine which IP segment we are editing
        ip_segments_str = self.get_ip_from_segments().split(".")
        current_segment = int(ip_segments_str[segment_index])

        # Make sure the segment is within the valid range
        if current_segment > 255:
            self.ip_segments[segment_index * 4] = "2"
            self.ip_segments[segment_index * 4 + 1] = "5"
            self.ip_segments[segment_index * 4 + 2] = "5"
        elif current_segment < 1:
            self.ip_segments[segment_index * 4] = "0"
            self.ip_segments[segment_index * 4 + 1] = "0"
            self.ip_segments[segment_index * 4 + 2] = "1"
        elif current_segment > 199 and self.ip_segments[segment_index * 4] == "2":
            if current_segment > 255:
                self.ip_segments[segment_index * 4 + 1] = "5"
                self.ip_segments[segment_index * 4 + 2] = "5"

    def select_item(self):
        if self.selected_index < len(self.ip_segments):
            self.edit_mode = not self.edit_mode
            self.display()
        elif self.selected_index == len(self.ip_segments):
            global back
            back()
        elif self.selected_index == len(self.ip_segments) + 1:
            self.submit_button_pressed()

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

    def submit_button_pressed(self):
        ip_to_submit = self.get_ip_from_segments()

        segments = ip_to_submit.split(".")

        for i, segment in enumerate(segments):
            cleaned_segment = str(int(segment))
            segments[i] = cleaned_segment
        ip_to_submit = ".".join(segments)

        if self.is_valid_ip(ip_to_submit):
            print("Submit button pressed with valid IP:", ip_to_submit)
            self.callback(ip_to_submit)
            self.draw.rectangle((0, 0, width, height), outline=0, fill=0)
            self.draw.text((2, 0), "IP CHANGED!", font=self.font, fill=255)
            oled.image(self.image)
            oled.show()
            global back
            back()

        else:
            print("Invalid IP address entered:", ip_to_submit)
            self.draw.rectangle((0, 0, width, height), outline=0, fill=0)
            self.draw.text((2, 0), "Invalid IP", font=self.font, fill=255)
            oled.image(self.image)
            oled.show()


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
                if filename.startswith("menu."):
                    screen_num = int(filename.split(".")[1])
                    with open(os.path.join(self.menu_folder, filename), "r") as f:
                        menu_lines = f.readlines()
                        menu_name = (
                            "Peitsman - " + menu_lines[0].strip()
                        )  # Read menu name from first line
                        menus[screen_num] = [
                            line.strip().split(",") for line in menu_lines[1:]
                        ]  # Exclude first line
                        menus[screen_num].insert(
                            0, [menu_name, "999"]
                        )  # Insert menu title as first item
        except FileNotFoundError as e:
            print(f"Error: {e}")
            raise
        return menus

    def display_menu(self):
        global oled, image, draw, font
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        # Draw menu title
        draw.text(
            (2, 0), self.menu_data[self.current_screen][0][0], font=font, fill=255
        )

        menu = self.menu_data[self.current_screen][
            1:
        ]  # Exclude the title from menu items
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_items, len(menu))

        for i in range(start_idx, end_idx):
            if start_idx <= self.selected_index < end_idx:
                if i == self.selected_index:
                    draw.rectangle(
                        (
                            0,
                            16 + (i - start_idx) * 16,
                            width,
                            16 + (i - start_idx + 1) * 16,
                        ),
                        outline=255,
                        fill=255,
                    )
                    if menu[i][1] == "997":
                        draw.text(
                            (2, 16 + (i - start_idx) * 16),
                            functions.function_handlers[menu[i][2]](),
                            font=font,
                            fill=0,
                        )
                    else:
                        draw.text(
                            (2, 16 + (i - start_idx) * 16),
                            menu[i][0],
                            font=font,
                            fill=0,
                        )
                else:
                    if menu[i][1] == "997":
                        draw.text(
                            (2, 16 + (i - start_idx) * 16),
                            functions.function_handlers[menu[i][2]](),
                            font=font,
                            fill=255,
                        )
                    else:
                        draw.text(
                            (2, 16 + (i - start_idx) * 16),
                            menu[i][0],
                            font=font,
                            fill=255,
                        )

        oled.image(image)
        oled.show()

    def select_item(self):
        item = self.menu_data[self.current_screen][self.selected_index + 1]
        flag = int(item[1])
        if flag == 999 or flag == 997:
            # self.display_menu()
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
            self.scroll_offset = max(
                0, len(self.menu_data[self.current_screen]) - self.visible_items - 1
            )
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


def back():
    global current_menu
    current_menu = menu_system
    menu_system.display_menu()


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
    # global current_menu
    current_menu.select_item()


def rotary_encoder(value, direction):
    # global current_menu
    if direction == "R":
        current_menu.next_item()
    elif direction == "L":
        current_menu.prev_item()


# Initialize encoder
encoder = Encoder(6, 13, 5, rotary_encoder, button_select_pressed)

satellite = Satellite()

# Main loop
try:
    while True:
        menu_system.check_lock_screen()
        time.sleep(0.1)
except KeyboardInterrupt:
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((5, height // 2 - 8), "Offline", font=font, fill=255)
    oled.image(image)
    oled.show()
    GPIO.cleanup()
