import os
import psutil
from PI import IPChanger
import json
ip_changer_instance = IPChanger()
def CPU_load():
    return psutil.cpu_percent(interval=1)

def CPU_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
            temperature = float(file.read().strip()) / 1000.0
            return round(temperature, 2)
    except FileNotFoundError:
        return None
# Function to get the menu name
def get_menu_name(menu_value, current_menu):
    for key, value in current_menu.items():
        if value == menu_value:
            return key
        elif isinstance(value, dict):
            result = get_menu_name(menu_value, value)
            if result is not None:
                return result

def edit_menu_DHCP(DHCP, current_menu):
    if DHCP:
        ip_changer_instance.set_ipv4_method_auto()
        DHCP = ip_changer_instance.get_ipv4_configuration_method()
        if DHCP:
            try:
                # If DHCP is enabled, hide IP Address and Subnet settings
                del current_menu["IP Address"]
                del current_menu["Subnet Mask"]
            except:
                pass
        else:
            try:
                del current_menu["Back"]
                current_menu["IP Address"] = None
                current_menu["Subnet Mask"] = None
                current_menu["Back"] = None
            except:
                pass
    else:
        # If DHCP is disabled, show IP Address and Subnet settings
        ip_changer_instance.set_ipv4_method_manual()
        DHCP = ip_changer_instance.get_ipv4_configuration_method()
        if DHCP:
            try:
                # If DHCP is enabled, hide IP Address and Subnet settings
                del current_menu["IP Address"]
                del current_menu["Subnet Mask"]
            except:
                pass
        else:
            try:
                del current_menu["Back"]
                current_menu["IP Address"] = None
                current_menu["Subnet Mask"] = None
                current_menu["Back"] = None
            except:
                pass
def check_code(code):
    with open('/home/peitsman/Streamdeck Companion project/Config.json', 'r') as file:
        config = json.load(file)

    lock_Pin = config.get('lock_pin', '')
    service_pin = config.get('service_pin', '')

    if code == lock_Pin:
        return "accept"
    elif code == service_pin:
        return "accept"
    else: 
        return None
def change_code(new_code):
    with open('/home/peitsman/Streamdeck Companion project/Config.json', 'r') as file:
        config = json.load(file)

    config['lock_pin'] = new_code
    
    with open('/home/peitsman/Streamdeck Companion project/Config.json', 'w') as file:
        json.dump(config, file, indent=4)