#Streamdeck Companion project
#DEV: Stijn van Hees
#Update date: 4/2/2024
#VERSION: 1.4.2.24


#todo's:
#TODO update every 5 seconds main menu

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
import data
from PI import IPChanger, Pi, SatelliteConfigManager

def display_logo():
    image = Image.open("/home/peitsman/Streamdeck Companion project/image/peitsman black white.bmp").convert("1")
    oled.image(image)
    oled.show()
    time.sleep(5)

cpu_temperature = "CPU TEMP: {}C".format(data.CPU_temp())
cpu_load = "CPU LOAD: {}%".format(data.CPU_load())
with open('/home/peitsman/Streamdeck Companion project/Config.json', 'r') as file:
    config = json.load(file)

DHCP = config['DHCP']
Subnet = config['last_subnet']
Companion_IP_address = config['companion_ip']
ip_changer_instance = IPChanger()
satellite = SatelliteConfigManager("/boot/satellite-config")
satellite.start_service()

menu = OrderedDict([
    ("Main", OrderedDict([
        (cpu_temperature, None),
        (cpu_load, None),
        ("Settings", OrderedDict([
            ("Change IP", OrderedDict([
                ("Streamdeck IP", OrderedDict([
                    ("DHCP", None),
                    ("IP Address", None),
                    #("Subnet Mask", None),
                    ("Back", None),
                ])),
                ("Companion IP", OrderedDict([
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

# Screen Variables
width = 128
height = 64
line = 1 
highlight = 1
shift = 0
total_lines = 6
current_menu = menu["Main"]
menu_history = [menu["Main"]]
amount_lines = 0
update_time = 0

# SCREEN SETUP
oled_reset = digitalio.DigitalInOut(board.D4)
i2c = busio.I2C(board.SCL, board.SDA)
oled = adafruit_ssd1306.SSD1306_I2C(width, height, i2c, addr=0x3C, reset=oled_reset)
image = Image.new("1", (oled.width, oled.height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
display_logo()

# Set up GPIO pins
SW = 5
DT = 6
CLK = 13

GPIO.setmode(GPIO.BCM)
GPIO.setup(SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(DT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(CLK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

step_pin = GPIO.input(CLK)
direction_pin = GPIO.input(DT)
button_pin = GPIO.input(SW)

# for tracking the direction and button state
previous_value = True
button_down = False

#TODO find the best sleeptime
sleep_time = 0.007



# Timer and lock variables
last_interaction_time = time.time()
lock_timer = time.time()
lock_timeout = 30  # 30 seconds
screen_locked = False

#Network settings
DHCP = ip_changer_instance.get_ipv4_configuration_method()
data.edit_menu_DHCP(DHCP, menu["Main"]["Settings"]["Change IP"]["Streamdeck IP"])



def read_config():
    with open('/home/peitsman/Streamdeck Companion project/Config.json', 'r') as file:
        return json.load(file)

def write_config(config):
    with open('/home/peitsman/Streamdeck Companion project/Config.json', 'w') as file:
        json.dump(config, file)

#Update the variables
def update_variable():
    global cpu_temperature, cpu_load, DHCP
    cpu_temperature = data.CPU_temp()
    cpu_load = data.CPU_load()

    cpu_temperature = "CPU TEMP: {}C".format(data.CPU_temp())
    cpu_load = "CPU LOAD: {}%".format(data.CPU_load())

    # DHCP = ip_changer_instance.get_ipv4_configuration_method()
    # data.edit_menu_DHCP(DHCP, menu["Main"]["Settings"]["Change IP"]["Streamdeck IP"])

# Function to update the display with the current menu
def update_display(current_menu, shift, highlight = 1):
    global line, amount_lines
    line = 1
    line_height = 10
    draw.rectangle((0, 0, width, height), fill=0)
    oled.fill(0)
    # Draw the menu items
    for key, value in current_menu.items():
        if highlight == line:
            draw.rectangle((0, (line - 1) * line_height + 15, width, line_height + (line - 1) * line_height + 15), outline=1, fill=1)
            draw.text((0, (line - 1) * line_height + 15), ">", font=font, fill=0)
            draw.text((10, (line - 1) * line_height + 15), key, font=font, fill=0)
        else:
            draw.text((0, (line - 1) * line_height + 15), key, font=font, fill=1)
        line += 1

    amount_lines = line - 1

    # Initial display update
    Logo = "Peitsman | " + data.get_menu_name(current_menu, menu)
    draw.text((0, 0), Logo, font=font, fill=1)
    oled.image(image)
    oled.show()

def reboot_network_screen():
    draw.rectangle((0, 0, width, height), fill=0)
    oled.fill(0)
    draw.text((0, 0), "Peitsman | Network", font=font, fill=1)
    draw.text((0,20),"Restarting network...", font=font, fill=1)
    oled.image(image)
    oled.show()

def reboot_screen():
    draw.rectangle((0, 0, width, height), fill=0)
    oled.fill(0)
    draw.text((0, 0), "Peitsman | Restart", font=font, fill=1)
    draw.text((0,20)," Restarting PI...", font=font, fill=1)
    oled.image(image)
    oled.show()

def edit_streamdeck_ip():
    global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time
    current_ip = ip_changer_instance.get_ip_address()
    ip_sections = list(map(int, current_ip.split('.')))
    selected_piece = 1
    edit_ip_menu = True

    def display_streamdeck_ip(selected_piece):
        draw.rectangle((0, 0, width, height), fill=0)
        oled.fill(0)
        draw.text((0, 0), "Peitsman | Streamdeck IP", font=font, fill=1)
        x_offset = 0
        for index, section in enumerate(ip_sections):
            section_width = len(str(section))  # Initialize section_width here
            # Highlight the selected piece
            if selected_piece == index + 1:
                draw.rectangle((x_offset -1, 16, x_offset + section_width * 6, 26), outline=1, fill=1)
                draw.text((x_offset, 16), str(section), font=font, fill=0)
            else:
                draw.text((x_offset, 16), str(section), font=font, fill=1)
            # Add spacing between sections
            x_offset += section_width * 6 + 5
        if selected_piece == 5:
            draw.rectangle((0,50,64,60), fill =1)
            draw.text((20, 50), "Back", font=font, fill=0)
        else:
            draw.text((20, 50), "Back", font=font, fill=1)
        if selected_piece == 6:
            draw.rectangle((64,50,128,60), fill =1)
            draw.text((75, 50), "Submit", font=font, fill=0)
        else:
            draw.text((75, 50), "Submit", font=font, fill=1)
        oled.image(image)
        oled.show()


    display_streamdeck_ip(selected_piece)
    while edit_ip_menu:
        current_step_pin = GPIO.input(CLK)
        if previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left 
                if GPIO.input(DT) == False:
                    if selected_piece > 1:
                        selected_piece -= 1  
                    else: 
                        selected_piece = 6
                # Turned Right 
                else:
                    if selected_piece < 6:
                        selected_piece += 1
                    else: 
                        selected_piece = 1
                display_streamdeck_ip(selected_piece)
            last_interaction_time = time.time()
            previous_value = current_step_pin
        current_button_pin = GPIO.input(SW)

        if current_button_pin == False and not button_down:
            button_down = True

        if current_button_pin == True and button_down:
            button_down = False
            last_interaction_time = time.time()
            if selected_piece == 5:
                edit_ip_menu = False
            elif selected_piece == 6:
                edit_ip_menu = False
                new_ip = '.'.join(map(str, ip_sections))
                reboot_network_screen()
                ip_changer_instance.set_ipv4_address(new_ip)
                Pi().restart_network()

            else:
                editing_ip = True
                while editing_ip:
                    current_step_pin = GPIO.input(CLK)
                    if previous_value != current_step_pin:
                        if current_step_pin == False:
                            # Turned Left 
                            if GPIO.input(DT) == False:
                                if ip_sections[selected_piece - 1] > 1:
                                    ip_sections[selected_piece - 1] -= 1  
                                else: 
                                    ip_sections[selected_piece - 1] = 255
                            # Turned Right 
                            else:
                                if ip_sections[selected_piece - 1] < 255:
                                    ip_sections[selected_piece - 1] += 1
                                else: 
                                    ip_sections[selected_piece - 1] = 1
                            display_streamdeck_ip(selected_piece)
                        last_interaction_time = time.time()
                        previous_value = current_step_pin
                    current_button_pin = GPIO.input(SW)

                    if current_button_pin == False and not button_down:
                        button_down = True

                    if current_button_pin == True and button_down:
                        button_down = False
                        last_interaction_time = time.time()
                        editing_ip = False
                    time.sleep(sleep_time)
        time.sleep(sleep_time)

    # Update the display to highlight the selected piece
    highlight = 1
    update_display(current_menu, 0, 1)
 
def edit_streamdeck_DHCP():
    global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time
    selected_piece = 1
    selected = ip_changer_instance.get_ipv4_configuration_method()
    edit_DHCP = True
    def display_DHCP(selected_piece):
        draw.rectangle((0, 0, width, height), fill=0)
        oled.fill(0)
        draw.text((0, 0), "Peitsman | DHCP", font=font, fill=1)
        x_offset = 0
        
        if selected == True :
            if selected_piece == 1:
                draw.rectangle((0,20,128,30), fill =1)
                draw.text((0,20),">", font=font, fill=0)
                draw.text((54,20),"ON", font=font, fill=0)
            else:
                draw.text((0,20),">", font=font, fill=1)
                draw.text((54,20), "ON", font=font, fill=1)        
            if selected_piece == 2:
                draw.rectangle((0,30,128,40), fill =1)
                draw.text((49,30),"OFF", font=font, fill=0)
            else:
                draw.text((49,30), "OFF", font=font, fill=1)
        else:
            if selected_piece == 1:
                draw.rectangle((0,20,128,30), fill =1)
                draw.text((54,20),"ON", font=font, fill=0)
            else:
                draw.text((54,20), "ON", font=font, fill=1)        
            if selected_piece == 2:
                draw.rectangle((0,30,128,40), fill =1)
                draw.text((0,30),">", font=font, fill=0)
                draw.text((49,30),"OFF", font=font, fill=0)
            else:
                draw.text((0,30),">", font=font, fill=1)
                draw.text((49,30), "OFF", font=font, fill=1)   
                       
        if selected_piece == 3:
            draw.rectangle((0,50,64,60), fill =1)
            draw.text((20, 50), "Back", font=font, fill=0)
        else:
            draw.text((20, 50), "Back", font=font, fill=1)
        if selected_piece == 4:
            draw.rectangle((64,50,128,60), fill =1)
            draw.text((75, 50), "Submit", font=font, fill=0)
        else:
            draw.text((75, 50), "Submit", font=font, fill=1)
        oled.image(image)
        oled.show()
    display_DHCP(selected_piece)
    while edit_DHCP:
        current_step_pin = GPIO.input(CLK)
        if previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left 
                if GPIO.input(DT) == False:
                    if selected_piece > 1:
                        selected_piece -= 1  
                    else: 
                        selected_piece = 4
                # Turned Right 
                else:
                    if selected_piece < 4:
                        selected_piece += 1
                    else: 
                        selected_piece = 1
                display_DHCP(selected_piece)
            last_interaction_time = time.time()
            previous_value = current_step_pin
        current_button_pin = GPIO.input(SW)

        if current_button_pin == False and not button_down:
            button_down = True


        if current_button_pin == True and button_down:
            last_interaction_time = time.time()
            button_down = False
            if selected_piece == 1:
                selected = True
            elif selected_piece == 2:
                selected = False
            elif selected_piece ==3:
                edit_DHCP = False
            elif selected_piece == 4:
                edit_DHCP = False
                reboot_network_screen()
                data.edit_menu_DHCP(selected, current_menu)
                Pi().restart_network()
            display_DHCP(selected_piece)
          
        time.sleep(sleep_time)
    # Update the display to highlight the selected piece
    highlight = 1
    update_display(current_menu, 0, 1)

def edit_streamdeck_subnet():
    global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time
    current_subnet = ip_changer_instance.get_subnet_mask()
    subnet_parts = list(map(int, current_subnet.split('.')))
    selected_piece = 1
    edit_subnet_menu = True
    
    def display_streamdeck_subnet(selected_piece):
        draw.rectangle((0, 0, width, height), fill=0)
        oled.fill(0)
        draw.text((0, 0), "Peitsman | Subnet", font=font, fill=1)
        x_offset = 0
        for index, section in enumerate(subnet_parts):
            section_width = len(str(section))  # Initialize section_width here
            # Highlight the selected piece
            if selected_piece == index + 1:
                draw.rectangle((x_offset -1, 16, x_offset + section_width * 6, 26), outline=1, fill=1)
                draw.text((x_offset, 16), str(section), font=font, fill=0)
            else:
                draw.text((x_offset, 16), str(section), font=font, fill=1)
            # Add spacing between sections
            x_offset += section_width * 6 + 5
        if selected_piece == 5:
            draw.rectangle((0,50,64,60), fill =1)
            draw.text((20, 50), "Back", font=font, fill=0)
        else:
            draw.text((20, 50), "Back", font=font, fill=1)
        if selected_piece == 6:
            draw.rectangle((64,50,128,60), fill =1)
            draw.text((75, 50), "Submit", font=font, fill=0)
        else:
            draw.text((75, 50), "Submit", font=font, fill=1)
        oled.image(image)
        oled.show()
    display_streamdeck_subnet(selected_piece)
    while edit_subnet_menu:
        current_step_pin = GPIO.input(CLK)
        if previous_value != current_step_pin:
            if current_step_pin == False:
                if GPIO.input(DT) == False:
                    if selected_piece > 1:
                        selected_piece -= 1  
                    else: 
                        selected_piece = 6
                else:
                    if selected_piece < 6:
                        selected_piece += 1
                    else: 
                        selected_piece = 1
                display_streamdeck_subnet(selected_piece)
            last_interaction_time = time.time()
            previous_value = current_step_pin
        current_button_pin = GPIO.input(SW)

        if current_button_pin == False and not button_down:
            button_down = True

        if current_button_pin == True and button_down:
            button_down = False
            last_interaction_time = time.time()
            if selected_piece == 5:
                edit_subnet_menu = False
            elif selected_piece == 6:
                edit_subnet_menu = False
                new_subnet_mask = '.'.join(map(str, subnet_parts))
                reboot_network_screen()
                ip_changer_instance.set_subnet_mask(new_subnet_mask)
                Pi().restart_network()
            else:
                editing_subnet = True
                while editing_subnet:
                    current_step_pin = GPIO.input(CLK)
                    if previous_value != current_step_pin:
                        if current_step_pin == False:
                            if GPIO.input(DT) == False:
                                if subnet_parts[selected_piece - 1] > 1:
                                    subnet_parts[selected_piece - 1] -= 1  
                                else: 
                                    subnet_parts[selected_piece - 1] = 255
                            else:
                                if subnet_parts[selected_piece - 1] < 255:
                                    subnet_parts[selected_piece - 1] += 1
                                else: 
                                    subnet_parts[selected_piece - 1] = 1
                            display_streamdeck_subnet(selected_piece)
                        last_interaction_time = time.time()
                        previous_value = current_step_pin
                    current_button_pin = GPIO.input(SW)

                    if current_button_pin == False and not button_down:
                        button_down = True

                    if current_button_pin == True and button_down:
                        button_down = False
                        last_interaction_time = time.time()
                        editing_subnet = False
                    time.sleep(sleep_time)
        time.sleep(sleep_time)

def edit_companion_ip():
    global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time
    current_ip = satellite.load_companion_ip()
    ip_sections = list(map(int, current_ip.split('.')))
    selected_piece = 1
    edit_ip_menu = True

    def display_companion_ip(selected_piece):
        draw.rectangle((0, 0, width, height), fill=0)
        oled.fill(0)
        draw.text((0, 0), "Peitsman | Companion IP", font=font, fill=1)
        x_offset = 0
        for index, section in enumerate(ip_sections):
            section_width = len(str(section))  # Initialize section_width here
            # Highlight the selected piece
            if selected_piece == index + 1:
                draw.rectangle((x_offset -1, 16, x_offset + section_width * 6, 26), outline=1, fill=1)
                draw.text((x_offset, 16), str(section), font=font, fill=0)
            else:
                draw.text((x_offset, 16), str(section), font=font, fill=1)
            # Add spacing between sections
            x_offset += section_width * 6 + 5
        if selected_piece == 5:
            draw.rectangle((0,50,64,60), fill =1)
            draw.text((20, 50), "Back", font=font, fill=0)
        else:
            draw.text((20, 50), "Back", font=font, fill=1)
        if selected_piece == 6:
            draw.rectangle((64,50,128,60), fill =1)
            draw.text((75, 50), "Submit", font=font, fill=0)
        else:
            draw.text((75, 50), "Submit", font=font, fill=1)
        oled.image(image)
        oled.show()


    display_companion_ip(selected_piece)
    while edit_ip_menu:
        current_step_pin = GPIO.input(CLK)
        if previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left 
                if GPIO.input(DT) == False:
                    if selected_piece > 1:
                        selected_piece -= 1  
                    else: 
                        selected_piece = 6
                # Turned Right 
                else:
                    if selected_piece < 6:
                        selected_piece += 1
                    else: 
                        selected_piece = 1
                display_companion_ip(selected_piece)
            last_interaction_time = time.time()
            previous_value = current_step_pin
        current_button_pin = GPIO.input(SW)

        if current_button_pin == False and not button_down:
            button_down = True

        if current_button_pin == True and button_down:
            button_down = False
            last_interaction_time = time.time()
            if selected_piece == 5:
                edit_ip_menu = False
            elif selected_piece == 6:
                edit_ip_menu = False
                new_ip = '.'.join(map(str, ip_sections))
                satellite.change_companion_ip(new_ip)
                satellite.restart_service()

            else:
                editing_ip = True
                while editing_ip:
                    current_step_pin = GPIO.input(CLK)
                    if previous_value != current_step_pin:
                        if current_step_pin == False:
                            # Turned Left 
                            if GPIO.input(DT) == False:
                                if ip_sections[selected_piece - 1] > 1:
                                    ip_sections[selected_piece - 1] -= 1  
                                else: 
                                    ip_sections[selected_piece - 1] = 255
                            # Turned Right 
                            else:
                                if ip_sections[selected_piece - 1] < 255:
                                    ip_sections[selected_piece - 1] += 1
                                else: 
                                    ip_sections[selected_piece - 1] = 1
                            display_companion_ip(selected_piece)
                        last_interaction_time = time.time()
                        previous_value = current_step_pin
                    current_button_pin = GPIO.input(SW)

                    if current_button_pin == False and not button_down:
                        button_down = True

                    if current_button_pin == True and button_down:
                        button_down = False
                        last_interaction_time = time.time()
                        editing_ip = False
                    time.sleep(sleep_time)
        time.sleep(sleep_time)

    # Update the display to highlight the selected piece
    highlight = 1
    update_display(current_menu, 0, 1)

def edit_pass_menu():
    global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time, menu_history, current_menu
    selected_piece = 1
    input_code_menu = True
    code_list = [0,0,0,0]
    def edit_pass(selected_piece):
        draw.rectangle((0, 0, width, height), fill=0)
        oled.fill(0)
        draw.text((0, 0), "Peitsman | edit code", font=font, fill=1)
        
        # Calculate the starting X-coordinate to center the text
        total_width = sum([len(str(section)) * 6 for section in code_list]) + (len(code_list) - 1) * 5
        center_x = (128 - total_width) / 2
        x_offset = center_x
        for index, section in enumerate(code_list):
            
            section_width = len(str(section))  # Initialize section_width here
            # Highlight the selected piece
            if selected_piece == index + 1:
                draw.rectangle((x_offset -1, 20, x_offset + section_width * 6, 30), outline=1, fill=1)
                draw.text((x_offset, 20), str(section), font=font, fill=0)
            else:
                draw.text((x_offset, 20), str(section), font=font, fill=1)
            x_offset += section_width * 6 + 5 
        if selected_piece == 5:
            draw.rectangle((0,40,128,50), fill =1)
            draw.text((44, 40), "back", font=font, fill=0)
        else:
            draw.text((44, 40), "back", font=font, fill=1)
        if selected_piece == 6:
            draw.rectangle((0,50,128,60), fill =1)
            draw.text((46, 50), "Submit", font=font, fill=0)
        else:
            draw.text((46, 50), "Submit", font=font, fill=1)
        oled.image(image)
        oled.show()
    edit_pass(selected_piece)
    while input_code_menu:
        current_step_pin = GPIO.input(CLK)
        if previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left 
                if GPIO.input(DT) == False:
                    if selected_piece > 1:
                        selected_piece -= 1  
                    else: 
                        selected_piece = 6
                # Turned Right 
                else:
                    if selected_piece < 6:
                        selected_piece += 1
                    else: 
                        selected_piece = 1
                edit_pass(selected_piece)
            last_interaction_time = time.time()
            previous_value = current_step_pin
            oled.poweron()
        current_button_pin = GPIO.input(SW)

        if current_button_pin == False and not button_down:
            button_down = True
            oled.poweron()
        if current_button_pin == True and button_down:
            oled.poweron()
            button_down = False
            if selected_piece == 6:
                oled.poweron()
                code = ''.join(map(str, code_list))
                data.change_code(code)
                input_code_menu = False
            elif selected_piece == 5:
                # Navigate back to the previous menu
                input_code_menu = False
                current_menu = menu_history.pop()
                highlight = 1
                update_display(current_menu, 0, 1)
            else:
                editing_code = True 
                while editing_code:
                    current_step_pin = GPIO.input(CLK)
                    if previous_value != current_step_pin:
                        if current_step_pin == False:
                            # Turned Left 
                            if GPIO.input(DT) == False:
                                if code_list[selected_piece - 1] > 0:
                                    code_list[selected_piece - 1] -= 1  
                                else: 
                                    code_list[selected_piece - 1] = 9
                                oled.poweron()
                            # Turned Right 
                            else:
                                if code_list[selected_piece - 1] < 9:
                                    code_list[selected_piece - 1] += 1
                                else: 
                                    code_list[selected_piece - 1] = 0
                                oled.poweron()
                            edit_pass(selected_piece)
                        previous_value = current_step_pin
                        oled.poweron()
                    current_button_pin = GPIO.input(SW)
                    if current_button_pin == False and not button_down:
                        oled.poweron()
                        button_down = True
                    if current_button_pin == True and button_down:
                        oled.poweron()
                        button_down = False
                        editing_code = False
        if time.time() - last_interaction_time > lock_timeout and not screen_locked:      
            oled.poweroff()
        time.sleep(sleep_time)
        highlight = 1
    highlight = 1
    update_display(current_menu, 0, 1)

def load_new_display():
    global current_menu, highlight, menu_history
    selected_menu = list(current_menu.keys())[highlight - 1]
    if current_menu[selected_menu] is not None:
        # Navigate to the selected submenu
        if selected_menu == "Masterpin":
            lock = lock_menu(False, True)
            if lock:
                previous_menu = current_menu
                current_menu = current_menu[selected_menu]
                highlight = 1
                menu_history.append(previous_menu)
                update_display(current_menu, 0, 1)  

        else:    
            previous_menu = current_menu
            current_menu = current_menu[selected_menu]
            highlight = 1
            menu_history.append(previous_menu)
            update_display(current_menu, 0, 1)
    elif selected_menu == "Back" and len(menu_history) > 1:
        # Navigate back to the previous menu
        current_menu = menu_history.pop()
        highlight = 1
        update_display(current_menu, 0, 1)
    elif selected_menu == "IP Address":
        edit_streamdeck_ip()
    elif selected_menu == "DHCP":
        edit_streamdeck_DHCP()
    elif selected_menu == "Subnet Mask":
        edit_streamdeck_subnet()
    elif selected_menu == "IP address":
        edit_companion_ip()
    elif selected_menu == "Change Lock":
        edit_pass_menu()
    elif selected_menu == "Restart Network":
        reboot_network_screen()        
        Pi().restart_network()
    elif selected_menu == "Restart Companion":
        satellite.restart_service()

    elif selected_menu == "Restart PI":
        reboot_screen()
        Pi().reboot()       

def lock_menu(screen_off = True, back=False):
    global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time, menu_history, current_menu
    selected_piece = 1
    input_code_menu = True
    code_list = [0,0,0,0]
    if screen_off:
        oled.poweroff()
    def edit_code_display(selected_piece):
        draw.rectangle((0, 0, width, height), fill=0)
        oled.fill(0)
        draw.text((0, 0), "Peitsman | LOCKED", font=font, fill=1)
        total_width = sum([len(str(section)) * 6 for section in code_list]) + (len(code_list) - 1) * 5
        center_x = (128 - total_width) / 2
        x_offset = center_x
        for index, section in enumerate(code_list):
            section_width = len(str(section))
            # Highlight the selected piece
            if selected_piece == index + 1:
                draw.rectangle((x_offset - 1, 20, x_offset + section_width * 6, 30), outline=1, fill=1)
                draw.text((x_offset, 20), str(section), font=font, fill=0)
            else:
                draw.text((x_offset, 20), str(section), font=font, fill=1)
            x_offset += section_width * 6 + 5

        if back:
            if selected_piece == 5:
                draw.rectangle((0,40,128,50), fill =1)
                draw.text((44, 40), "back", font=font, fill=0)
            else:
                draw.text((44, 40), "back", font=font, fill=1)
            if selected_piece == 6:
                draw.rectangle((0,50,128,60), fill =1)
                draw.text((46, 50), "Submit", font=font, fill=0)
            else:
                draw.text((46, 50), "Submit", font=font, fill=1)
        else:
            if selected_piece == 5:
                draw.rectangle((0,50,128,60), fill =1)
                draw.text((46, 50), "Submit", font=font, fill=0)
            else:
                draw.text((46, 50), "Submit", font=font, fill=1)
        oled.image(image)
        oled.show()
    edit_code_display(selected_piece)
    
    def edit_code():
        global button_down, previous_value, step_pin, direction_pin, button_pin, highlight, last_interaction_time, menu_history, current_menu    
        editing_code = True
        while editing_code:
            current_step_pin = GPIO.input(CLK)
            if previous_value != current_step_pin:
                if current_step_pin == False:
                    # Turned Left 
                    if GPIO.input(DT) == False:
                        if code_list[selected_piece - 1] > 0:
                            code_list[selected_piece - 1] -= 1  
                        else: 
                            code_list[selected_piece - 1] = 9
                        oled.poweron()
                    # Turned Right 
                    else:
                        if code_list[selected_piece - 1] < 9:
                            code_list[selected_piece - 1] += 1
                        else: 
                            code_list[selected_piece - 1] = 0
                        oled.poweron()
                    edit_code_display(selected_piece)
                previous_value = current_step_pin
                oled.poweron()
            current_button_pin = GPIO.input(SW)
            if current_button_pin == False and not button_down:
                oled.poweron()
                button_down = True
            if current_button_pin == True and button_down:
                oled.poweron()
                button_down = False
                editing_code = False
            if time.time() - last_interaction_time > lock_timeout and not screen_locked:      
                editing_code = False
                lock_menu(current_menu, screen_off)
            time.sleep(sleep_time)


    while input_code_menu:
        current_step_pin = GPIO.input(CLK)
        if previous_value != current_step_pin:
            if current_step_pin == False:
                # Turned Left 
                if GPIO.input(DT) == False:
                    if selected_piece > 1:
                        selected_piece -= 1  
                    else: 
                        selected_piece = 6
                # Turned Right 
                else:
                    if selected_piece < 6:
                        selected_piece += 1
                    else: 
                        selected_piece = 1
                edit_code_display(selected_piece)
            last_interaction_time = time.time()
            previous_value = current_step_pin
            oled.poweron()
        current_button_pin = GPIO.input(SW)

        if current_button_pin == False and not button_down:
            button_down = True
            oled.poweron()
        if current_button_pin == True and button_down:
            oled.poweron()
            button_down = False
            if not back:
                if selected_piece == 5:
                    oled.poweron()
                    code = ''.join(map(str, code_list))
                    check = data.check_code(code)
                    if check == "accept":
                        input_code_menu = False
                        last_interaction_time = time.time()
                        return True
                elif selected_piece in [1, 2, 3, 4]:
                    edit_code()
            else:
                if selected_piece == 5:
                    # Navigate back to the previous menu
                    input_code_menu = False
                    current_menu = menu["Main"]
                    menu_history = [menu["Main"]]
                    highlight = 1
                    update_display(current_menu, 0, 1)
                elif selected_piece == 6:
                    oled.poweron()
                    code = ''.join(map(str, code_list))
                    check = data.check_code(code)
                    if check == "accept":
                        input_code_menu = False
                        last_interaction_time = time.time()
                        return True
                else:
                    edit_code()
        if time.time() - last_interaction_time > lock_timeout and not screen_locked:      
            oled.poweroff()
        time.sleep(sleep_time)
                   
                
#TODO DEV        
#DEV        
update_display(current_menu, shift, highlight)
lock_menu(False)

while True:

    # if time.time() - lock_timer > 5:
    #     update_variable()
    #     print("update")
    #     lock_timer = time.time()
    #     update_display(current_menu, shift, highlight)

    current_step_pin = GPIO.input(CLK)
    if previous_value != current_step_pin:
        if current_step_pin == False:
            # Turned Left 
            if GPIO.input(DT) == False:
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

            update_display(current_menu, shift, highlight)
        last_interaction_time = time.time()
        previous_value = current_step_pin
    current_button_pin = GPIO.input(SW)

    if current_button_pin == False and not button_down:
        button_down = True
        
    
    if current_button_pin == True and button_down:
        button_down = False
        last_interaction_time = time.time()
        load_new_display()

    if time.time() - last_interaction_time > lock_timeout and not screen_locked:      
        lock_menu()
    
    time.sleep(sleep_time)