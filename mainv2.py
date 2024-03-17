# Streamdeck Companion project
# DEV: Stijn van Hees
# Update date: 17/3/2024
# VERSION: 2.17.3.24


# todo's:
# TODO update every 5 seconds main menu

# - Lock Pin: 4848 (Deze kan via het menu worden aangepast indien gewenst)
# - Service Pin: 4592 (Deze kan alleen softwarematig veranderd worden)

import board
import busio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import time
import digitalio
import json
from collections import OrderedDict
import socket
import subprocess
import os
import re


class Display:
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
    
    def initialize_display(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.oled = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, self.i2c, addr=0x3C, reset=self.reset_pin)
        self.image = Image.new("1", (self.oled.width, self.oled.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()

    def display_logo(self, logo_path):
        image = Image.open(logo_path).convert("1")
        self.oled.image(image)
        self.oled.show()
        time.sleep(5)

    def clear_display(self):
        self.draw.rectangle((0, 0, self.width, self.height), fill=0)
        self.oled.fill(0)    

    def draw_text(self, text, position, font_color=1):
        self.draw.text(position, text, font=self.font, fill=font_color)

    def update_display(self):
        self.oled.image(self.image)
        self.oled.show()

class Menus:
    def __init__(self, display):
        self.menu = OrderedDict([
            ("Main", OrderedDict([
                ("Local IP", None),
                ("Remote IP", None),
                ("Settings", OrderedDict([
                    ("Change IP", OrderedDict([
                        ("Local IP", OrderedDict([
                            ("DHCP", None),
                            ("IP Address", None),
                            ("Back", None),
                        ])),
                        ("Remote IP", OrderedDict([
                            ("IP address", None),
                            ("Back", None),
                        ])),
                        ("Back", None),
                    ])),
                    ("Service", OrderedDict([
                        ("Masterpin", OrderedDict([
                            ("Change Lock", None),
                            ("Restart Network", None),
                            ("Restart Companion", None),
                            ("Restart PI", None),
                            ("Back", None),
                        ])),
                        ("Back", None),
                    ])),
                    ("Back", None),
                ])),
            ])),
        ])
        self.current_menu = self.menu["Main"]
        self.menu_history = [self.menu["Main"]]
        self.display = display

    def menu_name(self, menu_value, current_menu=None):
        current_menu = current_menu or self.current_menu  # Use current_menu if provided, otherwise use self.current_menu
        for key, value in current_menu.items():
            if value == menu_value:
                return key
            elif isinstance(value, dict):
                result = self.menu_name(menu_value, value)
                if result is not None:
                    return result
        return ""  # Terminate recursion if no match is found    
    def update_display(self, highlight = 1):
        self.display.clear_display()
        line = 1
        line_height = 10
        for key, value in self.current_menu.items():
            if highlight == line:
                self.display.draw.rectangle(
                    (0, (line - 1) * line_height + 15, self.display.width,
                     line_height + (line - 1) * line_height + 15),
                    outline=1,
                    fill=1,
                )
                self.display.draw.text((0, (line - 1) * line_height + 15), ">", font=self.display.font, fill=0)
                self.display.draw.text((10, (line - 1) * line_height + 15), key, font=self.display.font, fill=0)
            else:
                self.display.draw.text((0, (line - 1) * line_height + 15), key, font=self.display.font, fill=1)
            line += 1

        logo = "Peitsman | " + self.menu_name(self.current_menu)
        self.display.draw.text((0, 0), logo, font=self.display.font, fill=1)
        
        self.display.update_display()



class InputHandler:
    def __init__(self, clk_pin, dt_pin, sw_pin, lock_timeout, sleep_time, menu):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.lock_timeout = lock_timeout
        self.sleep_time = sleep_time
        self.menu = menu
        self.previous_value = True
        self.button_down = False
        self.last_interaction_time = time.time()
        self.counter = 0  # Initialize counter

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def handle_input(self):
        current_step_pin = GPIO.input(self.clk_pin)
        if self.previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left
                if GPIO.input(self.dt_pin) == False:
                    self.counter -= 1
                    print("Counter Decremented:", self.counter)

                # Turned Right
                else:
                    self.counter += 1
                    print("Counter Incremented:", self.counter)

                self.last_interaction_time = time.time()
                self.previous_value = current_step_pin

        current_button_pin = GPIO.input(self.sw_pin)
        if current_button_pin == False and not self.button_down:
            self.button_down = True

        if current_button_pin == True and self.button_down:
            self.button_down = False
            self.last_interaction_time = time.time()
            self.menu.load_new_display()

        if time.time() - self.last_interaction_time > self.lock_timeout:
            self.menu.lock_menu()

        time.sleep(self.sleep_time)

    def __init__(self, clk_pin, dt_pin, sw_pin, lock_timeout, sleep_time, menu):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.lock_timeout = lock_timeout
        self.sleep_time = sleep_time
        self.menu = menu
        self.previous_value = True
        self.button_down = False
        self.last_interaction_time = time.time()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def handle_input(self):
        current_step_pin = GPIO.input(self.clk_pin)
        if self.previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left
                if GPIO.input(self.dt_pin) == False:
                    if self.menu.highlight > 1:
                        self.menu.highlight -= 1
                    else:
                        self.menu.highlight = self.menu.amount_lines  

                # Turned Right
                else:
                    if self.menu.highlight < self.menu.amount_lines:
                        self.menu.highlight += 1
                    else:
                        self.menu.highlight = 1

                self.menu.update_display()
            self.last_interaction_time = time.time()
            self.previous_value = current_step_pin

        current_button_pin = GPIO.input(self.sw_pin)
        if current_button_pin == False and not self.button_down:
            self.button_down = True

        if current_button_pin == True and self.button_down:
            self.button_down = False
            self.last_interaction_time = time.time()
            self.menu.load_new_display()

        if time.time() - self.last_interaction_time > self.lock_timeout:
            self.menu.lock_menu()

        time.sleep(self.sleep_time)

class Lock:
    def __init__(self):
        # Initialize lock-related settings
        pass

    def check_lock(self):
        # Check if the system is locked and handle accordingly
        pass


class Network:
    def __init__(self):
        pass


class SatelliteConfigManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def change_companion_ip(self, new_ip):
        try:
            with open(self.file_path, "r") as config_file:
                lines = config_file.readlines()

            with open(self.file_path, "w") as config_file:
                for line in lines:
                    if line.startswith("# COMPANION_IP="):
                        print(line)
                        config_file.write(f"COMPANION_IP={new_ip}\n")
                        print(f"COMPANION_IP={new_ip}\n")
                    else:
                        config_file.write(line)
            print(f"COMPANION_IP changed to {new_ip}")
        except FileNotFoundError:
            print(f"File {self.file_path} not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def load_companion_ip(self):
        try:
            with open("/home/satellite/satellite-config.json") as f:
                config_data = json.load(f)
                print(config_data.get("remoteIp"))
                return config_data.get("remoteIp")
        except FileNotFoundError:
            print(f"File {'/home/satellite/satellite-config.json'} not found.")
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


class MenuSystem:
    def __init__(self):
        self.display = Display()
        self.menus = Menus(self.display)
        self.lock = Lock()
        self.network = Network()
        self.satellite = SatelliteConfigManager('/home/satellite/satellite-config.json')
        self.input_handler = InputHandler(
            clk_pin=17, dt_pin=18, sw_pin=27,
            lock_timeout=300, sleep_time=0.1,
            menu=self.menus
        )

        self.display.display_logo('/home/peitsman/Streamdeck Companion project/assets/peitsman black white.bmp')

    def run(self):
        self.menus.update_display()
        # while True:
        #     print(self.input_handler.handle_input())
        #     self.lock.check_lock()
        #     time.sleep(0.1)  # Adjust sleep time as needed


if __name__ == "__main__":
    menu_system = MenuSystem()
    menu_system.run()
