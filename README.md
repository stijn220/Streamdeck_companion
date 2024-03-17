Pi 64bit lite

https://github.com/bitfocus/companion-satellite/blob/main/README.md
curl https://raw.githubusercontent.com/bitfocus/companion-satellite/main/pi-image/install.sh | sh

sudo raspi-config
-	Interface Options > I2C > ON
-	Localisation Options > Timezone > Amsterdam

sudo apt update
sudo apt upgrade -y

sudo apt install python3 python3-pip network-manager -y
sudo rm /usr/lib/python3.11/EXTERNALLY-MANAGED

cd ~
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py

sudo python -m pip install --upgrade pip setuptools wheel sudo pip install Adafruit-SSD1306

sudo pip install adafruit-circuitpython-ssd1306

sudo pip install pillow

sudo pip install psutil

sudo service NetworkManager start

# Peitsman logo
cd /
sudo cp -f /home/peitsman/Streamdeck\ Companion\ project/assets/satellite/icon.png /usr/local/src/companion-satellite/assets/
sudo systemctl restart satellite

# boot py file on startup
sudo chmod 755 "/home/peitsman/Streamdeck Companion project/launcher.sh"