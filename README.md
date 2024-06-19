# Getting Started

## Prerequisites
- Raspberry Pi 4B
- MicroSD card
- Power supply for Raspberry Pi
- Internet connection
- Companion installed on a pc
- Streamdeck

### install the OS
install the latest version of [Pi 64bit lite](https://downloads.raspberrypi.com/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64-lite.img.xz) on the Raspberry Pi 4b. We recommend
\ to use the [Raspberry Pi Imager](https://downloads.raspberrypi.org/imager/imager_latest.exe)


### Setup the companion satellite

Read the [companion satelite documentation](https://github.com/bitfocus/companion-satellite/blob/main/README.md) for the latest update.


Part of the companion satellite documentation:

```
sudo -i
sudo curl https://raw.githubusercontent.com/bitfocus/companion-satellite/main/pi-image/install.sh | bash
```

To make sure the latest version is running, run:
```
sudo satellite-update
```


### Setup the python script

Open the Raspberry Pi configuration tool:

```
sudo raspi-config
```

Enable I2C:
- Go to Interface Options > I2C > ON

Set the timezone:
- Go to Localisation Options > Timezone > Europe > Amsterdam


Update and upgrade the system:
```
sudo apt update
sudo apt upgrade -y
```

Install Python and necessary packages:
```
sudo apt install python3 python3-pip network-manager -y
```

#IGNORE sudo rm /usr/lib/python3.11/EXTERNALLY-MANAGED

Navigate to the home directory and install additional Python libraries:
```
cd ~
sudo apt install git
pip3 install --upgrade adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo -E env PATH=$PATH python3 raspi-blinka.py
sudo python -m pip install --upgrade pip setuptools wheel
sudo pip install Adafruit-SSD1306 adafruit-circuitpython-ssd1306 pillow psuti
```

#sudo service NetworkManager start

### Import the script from github
```
cd
git clone https://github.com/stijn220/Streamdeck_companion.git
cd Streamdeck_companion
```

### setup the Peitsman logo
set the Peitsman logo as default on the streamdeck:
```
cd /

sudo cp -f /home/peitsman/Streamdeck_companion/assets/satellite/icon.png /usr/local/src/companion-satellite/satellite/assets/

sudo cp -f /home/peitsman/Streamdeck_companion/assets/satellite/tray.png /usr/local/src/companion-satellite/satellite/assets/

sudo cp -f /home/peitsman/Streamdeck_companion/assets/satellite/tray.ico /usr/local/src/companion-satellite/satellite/assets/

sudo systemctl restart satellite
```

### boot py file on startup
sudo chmod 755 "/home/peitsman/Streamdeck Companion project/launcher.sh"