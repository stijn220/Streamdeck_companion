#Streamdeck Companion project
#DEV: Stijn van Hees
#Update date: 18/3/2024
#VERSION: 2.18.3.24


#todo's:
#TODO update every 5 seconds main menu
#TODO Menu Title
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
from encoder import Encoder


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

    def reboot_network_screen(self):
        self.draw.text((0, 0), "Peitsman | Network", font=self.font, fill=1)
        self.draw.text((0,20),"Restarting network...", font=self.font, fill=1)

    def reboot_pi_screen(self):
        self.draw.text((0, 0), "Peitsman | Restart", font=self.font, fill=1)
        self.draw.text((0,20)," Restarting PI...", font=self.font, fill=1)

    

    def clear_display(self):
        self.draw.rectangle((0, 0, self.width, self.height), fill=0)
        self.oled.fill(0)    

    def draw_text(self, text, position, font_color=1):
        self.draw.text(position, text, font=self.font, fill=font_color)



    def update_display(self):
        self.oled.image(self.image)
        self.oled.show()

class Menus:
    def __init__(self, display, menu_systems):
        self.menu_system = menu_systems
        self.menu = OrderedDict([
            ("Main", OrderedDict([
                (f"IP {self.menu_system.get_ipv4_placeholder()}", None),
                (f"COM {self.menu_system.get_companion_ip()}", None),
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
        self.highlight = 1

    def update_display(self, highlight=1):
        self.highlight = highlight
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

    def menu_name(self, menu_value, current_menu=None):
        if current_menu is None:
            current_menu = self.current_menu
        for key, value in current_menu.items():
            if value == menu_value:
                return key
            elif isinstance(value, dict):
                result = self.menu_name(menu_value=menu_value, current_menu=value)
                if result is not None:
                    return result
        return 'None'

    def load_new_menu(self):
        selected_menu = list(self.current_menu.keys())[self.highlight - 1]
        if self.current_menu[selected_menu] is not None:
            previous_menu = self.current_menu
            self.current_menu = self.current_menu[selected_menu]
            menu_system.highlight = 1
            self.menu_history.append(previous_menu)
            self.update_display(1)
        elif selected_menu == "Back" and len(self.menu_history) > 1:
            self.current_menu = self.menu_history.pop()
            menu_system.highlight = 1
            self.update_display(1)
        elif selected_menu == f"IP {self.menu_system.get_ipv4_placeholder()}" or selected_menu == "IP Address":
            print('Streamdeck IP')
            #TODO edit_streamdeck_ip()
        elif selected_menu == f"COM {self.menu_system.get_companion_ip()}" or selected_menu == "IP address":
            print('companion IP')
            #TODO edit_companion_ip()
        elif selected_menu == "DHCP":
            print("DHCP")
            #TODO DHCP
        elif selected_menu == "Change Lock":
            print("Lock")
            #TODO edit_pass_menu()
        elif selected_menu == "Restart Network":
            print("Restart Network")
            #TODO reboot_network_screen()        
            #TODO Pi().restart_network()
        elif selected_menu == "Restart Companion":
            print('Restart Companion')
            #TODO satellite.restart_service()
        elif selected_menu == "Restart PI":
            print('Restart Pi')
            #TODO reboot_screen()
            #TODO Pi().reboot()       

class Lock:
    def __init__(self):
        # Initialize lock-related settings
        pass

    def check_lock(self):
        # Check if the system is locked and handle accordingly
        pass

class NetworkManager:
    def __init__(self, connection_name='Wired\ connection\ 1'):
        self.connection_name = connection_name
        self.connection_file = f"/etc/NetworkManager/system-connections/{self.connection_name}.nmconnection"
        self.previous_ip = None

    def get_ipv4(self):
        result = os.popen(f"nmcli -g IP4.ADDRESS connection show {self.connection_name}").read().strip()
        ip_address = result.split("/")[0]
        return ip_address

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
        self.network = NetworkManager() 
        self.lock = Lock()
        self.satellite = SatelliteConfigManager('/home/satellite/satellite-config.json')
        self.highlight = 1
        self.encoder = Encoder(6, 13, 5, self.update, self.button)
        #self.display.display_logo('/home/peitsman/Streamdeck Companion project/assets/peitsman black white.bmp')
        self.menus = Menus(self.display, self)

    def update(self, value, direction):
        if direction == "R":
            self.highlight += 1
            if self.highlight > len(self.menus.current_menu):
                self.highlight = 1
        elif direction == "L":
            self.highlight -= 1
            if self.highlight < 1:
                self.highlight = len(self.menus.current_menu)
        self.menus.update_display(self.highlight)

    def get_ipv4_placeholder(self):
        ip = self.network.get_ipv4()
        return ip

    def get_companion_ip(self):
        ip = self.satellite.load_companion_ip()
        return ip

    def button(self):
        self.menus.load_new_menu()

    def run(self):
        self.menus.update_display()
        while True:
            time.sleep(0.1)
            #self.lock.check_lock()

if __name__ == "__main__":
    menu_system = MenuSystem()
    menu_system.run()
