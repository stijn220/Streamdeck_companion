import socket
import subprocess
import json
import os
import re


class IPChanger:
    def __init__(self, connection_name='Wired connection 1'):
        self.connection_name = connection_name
        self.config_path = "/home/peitsman/Streamdeck Companion project/Config.json"

    def get_ip_address(self, interface = eth0):
        #Get the current IP address of the system.
        try:
            result = subprocess.run(["ip", "addr", "show", self.interface], capture_output=True, text=True, check=True)
            # Use regular expression to extract the IPv4 address
            match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', result.stdout)
            if match:
                ip_address = match.group(1)
                return ip_address
            else:
                return None
        except subprocess.CalledProcessError:
            print(f"Error: Unable to retrieve IP address for interface {self.connection_name}")
            return None


    def get_ipv4_configuration_method(self):
        #Check whether DHCP is enabled for a specified network interface.
        try:
            # Run sudo nmcli command to show only the ipv4.method property
            result = subprocess.run(['sudo', 'nmcli', '-g', 'ipv4.method', 'connection', 'show', self.connection_name], capture_output=True, text=True, check=True)

            
            # Extract the configuration method
            method = result.stdout.strip()
            if method == "auto":
                return True
            else: 
                return False

        except subprocess.CalledProcessError as e:
            return f"Error: {e}"
    
    def get_subnet_mask(self):
        return '255.255.255.0'
    #TODO get subnet mask

    def set_ipv4_method_manual(self):
        #Set the IPv4 method to manual using the configuration file.
        try:
            with open(self.config_path, 'r') as file:
                config = json.load(file)
            last_ip = config.get('last_ip', '')
            subprocess.run(['sudo', 'nmcli', 'connection', 'modify', self.connection_name, 'ipv4.method', 'manual', 'ipv4.address', f'{last_ip}/24'])
            #sudo nmcli connection modify 'Wired connection 1' ipv4.method manual
        except (json.JSONDecodeError, FileNotFoundError, subprocess.CalledProcessError) as e:
            raise ValueError(f"Error setting manual IP: {e}")

    def set_ipv4_method_auto(self):
        #Set the IPv4 method to automatic.
        try:
            subprocess.run(['sudo', 'nmcli', 'connection', 'modify', self.connection_name, 'ipv4.method', 'auto'])
            #sudo nmcli connection modify 'Wired connection 1' ipv4.method auto
            subprocess.run(['sudo', 'dhclient', '-r'])
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error setting automatic IP: {e}")

    def set_ipv4_address(self, ip_address, subnet_mask='24'):
        try:
            # Update the configuration file with the new IP address
            with open(self.config_path, 'r') as file:
                config = json.load(file)
                config['last_ip'] = ip_address

            with open(self.config_path, 'w') as file:
                json.dump(config, file)

            # Set the new IPv4 address using nmcli
            subprocess.run(['sudo', 'nmcli', 'connection', 'modify', self.connection_name, 'ipv4.address', f'{ip_address}/24'], check=True)
            #subprocess.run(['sudo', 'nmcli', 'connection', 'modify', self.connection_name, 'ipv4.addresses', ip_address])

            #sudo nmcli connection modify 'Wired connection 1' ipv4.address 192.168.1.240/24

        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(f"Error setting IPv4 address: {e}")
    def set_subnet_mask(self, new_subnet_mask):
        try:
            # Update the configuration file with the new subnet mask
            with open(self.config_path, 'r') as file:
                config = json.load(file)
                config['last_subnet'] = new_subnet_mask

            with open(self.config_path, 'w') as file:
                json.dump(config, file)

            # Set the new subnet mask using nmcli
            subprocess.run(['sudo', 'nmcli', 'connection', 'modify', self.connection_name, 'ipv4.address', f'{config["last_ip"]}/{new_subnet_mask}'], check=True)
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            raise ValueError(f"Error setting subnet mask: {e}")

class SatelliteConfigManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def change_companion_ip(self, new_ip):
        try:
            with open(self.file_path, 'r') as config_file:
                lines = config_file.readlines()

            with open(self.file_path, 'w') as config_file:
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
            with open('/home/satellite/satellite-config.json') as f:
                config_data = json.load(f)
                print(config_data.get('remoteIp'))
                return config_data.get('remoteIp')
        except FileNotFoundError:
            print(f"File {'/home/satellite/satellite-config.json'} not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
    
    def start_service(self):
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'satellite'])
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error rebooting: {e}")
    def restart_service(self):
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'satellite'])
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error rebooting: {e}")

class Pi:
    def reboot(self):
        #Initiate a system reboot.
        try:
            subprocess.run(['sudo', 'reboot'])
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error rebooting: {e}")

    def restart_network(self, connection_name='Wired connection 1'):
        #Restart the network for the specified connection.
        try:
            subprocess.run(['sudo', 'nmcli', 'connection', 'down', connection_name])
            subprocess.run(['sudo', 'nmcli', 'connection', 'up', connection_name])
        except Exception as e:
            print(f"Error rebooting network: {e}")