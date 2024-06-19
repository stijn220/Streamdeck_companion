import time
import board
import busio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import globalsetting
from myFunctions import functionHandlersDictionary
from myClasses import myButton, myButtonsList

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

    def load_menus(self):
        menus = {}
        for filename in sorted(os.listdir(self.menu_folder)):
            if filename.startswith('menu.'):
                screen_num = int(filename.split('.')[1])
                with open(os.path.join(self.menu_folder, filename), 'r') as f:
                    menus[screen_num] = [line.strip().split(',') for line in f.readlines()]
        return menus

    def display_menu(self):
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        menu = self.menu_data[self.current_screen]
        for i, item in enumerate(menu):
            if i == self.selected_index:
                draw.rectangle((0, i * 16, width, (i + 1) * 16), outline=255, fill=255)
                draw.text((2, i * 16), item[0], font=font, fill=0)
            else:
                draw.text((2, i * 16), item[0], font=font, fill=255)
        oled.image(image)
        oled.show()

    def select_item(self):
        item = self.menu_data[self.current_screen][self.selected_index]
        flag = int(item[1])
        if flag == 999:
            return  # informational, do nothing
        elif flag == 998:
            functionHandlersDictionary[item[2]]()
        else:
            self.current_screen = flag
        self.selected_index = 0
        self.last_interaction_time = time.time()

    def next_item(self):
        self.selected_index = (self.selected_index + 1) % len(self.menu_data[self.current_screen])
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
def button_next_pressed(channel):
    menu_system.next_item()

def button_select_pressed(channel):
    menu_system.select_item()

GPIO.setmode(GPIO.BCM)
GPIO.setup(globalsetting.BUTTON_NEXT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(globalsetting.BUTTON_SELECT, GPIO.IN, pull_up_down=GPIO.PUD_UP)

GPIO.add_event_detect(globalsetting.BUTTON_NEXT, GPIO.FALLING, callback=button_next_pressed, bouncetime=200)
GPIO.add_event_detect(globalsetting.BUTTON_SELECT, GPIO.FALLING, callback=button_select_pressed, bouncetime=200)

try:
    while True:
        menu_system.check_lock_screen()
        time.sleep(1)
except KeyboardInterrupt:
    GPIO.cleanup()
