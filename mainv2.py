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

class Menu:
    def __init__(self):
        # Initialize menu structure and variables
        pass

    def load_new(self):
        # Load a new display based on the current selection
        pass


class InputHandler:
    def __init__(self, clk_pin, dt_pin, sw_pin, lock_timeout, sleep_time):
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin
        self.lock_timeout = lock_timeout
        self.sleep_time = sleep_time
        self.previous_value = True
        self.button_down = False
        self.last_interaction_time = time.time()

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.sw_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def handle_input(self, update_display_func, load_new_display_func, lock_menu_func):
        current_step_pin = GPIO.input(self.clk_pin)
        if self.previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left 
                if GPIO.input(self.dt_pin) == False:
                    if highlight > 1:
                        highlight -= 1
                    else:
                        highlight = amount_lines  

                # Turned Right
                else:
                    if highlight < amount_lines:
                        highlight += 1
                    else:
                        highlight = 1

                update_display_func()
            self.last_interaction_time = time.time()
            self.previous_value = current_step_pin

        current_button_pin = GPIO.input(self.sw_pin)
        if current_button_pin == False and not self.button_down:
            self.button_down = True

        if current_button_pin == True and self.button_down:
            self.button_down = False
            self.last_interaction_time = time.time()
            load_new_display_func()

        if time.time() - self.last_interaction_time > self.lock_timeout:
            lock_menu_func()

        time.sleep(sleep_time)


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
        self.display = Display(self.menu)
        self.menu = Menu()
        self.input_handler = InputHandler()
        self.lock = Lock()
        self.network = Network()
        self.satellite = SatelliteConfigManager()

    def setup(self):
        with open(
            "/home/peitsman/Streamdeck Companion project/Config.json", "r"
        ) as file:
            self.config = json.load(file)

        self.menu = OrderedDict([
            ("Main", OrderedDict([
                (local_ip, None),
                (remote_ip, None),
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

        self.display.display_logo()

    def run(self):
        while True:
            self.input_handler.handle_input()
            self.lock.check_lock()
            time.sleep(0.1)  # Adjust sleep time as needed


# if __name__ == "__main__":
#     menu_system = MenuSystem()
#     menu_system.setup()
#     menu_system.run()
