import os
import subprocess
import re

class PiNetwork:
    def __init__(self, interface='eth0'):
        self.interface = interface
        self.dhcpcd_conf = '/etc/dhcpcd.conf'
        self.backup_conf = '/etc/dhcpcd.conf.bak'
        self.last_static_ip = None
        
        # Ensure dhcpcd_conf file exists or create it
        if not os.path.exists(self.dhcpcd_conf):
            print(f"{self.dhcpcd_conf} not found. Creating a new file...")
            try:
                with open(self.dhcpcd_conf, 'w') as f:
                    f.write("# Initial dhcpcd.conf file\n")
            except OSError as e:
                print(f"Error creating {self.dhcpcd_conf}: {e}")
            else:
                print(f"{self.dhcpcd_conf} created successfully.")

    def backup_config(self):
        if os.path.exists(self.dhcpcd_conf) and not os.path.exists(self.backup_conf):
            with open(self.dhcpcd_conf, 'r') as original, open(self.backup_conf, 'w') as backup:
                backup.write(original.read())
    
    def restore_backup(self):
        if os.path.exists(self.backup_conf):
            with open(self.backup_conf, 'r') as backup, open(self.dhcpcd_conf, 'w') as original:
                original.write(backup.read())

    def get_current_gateway(self):
        result = subprocess.run(['ip', 'route'], capture_output=True, text=True)
        match = re.search(r'default via ([\d.]+)', result.stdout)
        return match.group(1) if match else None

    def get_current_dns(self):
        dns_servers = []
        if os.path.exists('/etc/resolv.conf'):
            with open('/etc/resolv.conf', 'r') as f:
                lines = f.readlines()
            for line in lines:
                match = re.match(r'nameserver ([\d.]+)', line)
                if match:
                    dns_servers.append(match.group(1))
        return dns_servers
    
    def set_static_ip(self, ip_address, gateway=None, dns_servers=None):
        if not os.path.exists(self.dhcpcd_conf):
            print(f"{self.dhcpcd_conf} not found. Unable to set static IP.")
            return

        if gateway is None:
            gateway = self.get_current_gateway()
        if dns_servers is None:
            dns_servers = self.get_current_dns()
        
        self.last_static_ip = ip_address  # Store the last static IP
        self.backup_config()
        static_ip_conf = f"""
interface {self.interface}
static ip_address={ip_address}/24
static routers={gateway}
static domain_name_servers={','.join(dns_servers)}
"""

        with open(self.dhcpcd_conf, 'a') as f:
            f.write(static_ip_conf)
        
        # Restart the network service to apply changes
        try:
            subprocess.run(['sudo', 'systemctl', 'status', 'dhcpcd'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'], check=True)
            print(f"Static IP set to {ip_address} for interface {self.interface}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to restart dhcpcd: {e}")

    def enable_dhcp(self):
        if not os.path.exists(self.dhcpcd_conf):
            print(f"{self.dhcpcd_conf} not found. Unable to enable DHCP.")
            return

        self.backup_config()
        self.restore_backup()
        
        # Restart the network service to apply changes
        try:
            subprocess.run(['sudo', 'systemctl', 'status', 'dhcpcd'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', 'dhcpcd'], check=True)
            print(f"DHCP enabled for interface {self.interface}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to restart dhcpcd: {e}")

    def disable_dhcp(self):
        if self.last_static_ip is None:
            print("No previous static IP found.")
            return
        self.set_static_ip(self.last_static_ip)
        print(f"Static IP restored to {self.last_static_ip}")

    def get_current_ip(self):
        result = subprocess.run(['ip', 'addr', 'show', self.interface], capture_output=True, text=True)
        match = re.search(r'inet ([\d.]+)/\d+', result.stdout)
        return match.group(1) if match else None

    def get_dhcp_state(self):
        if not os.path.exists(self.dhcpcd_conf):
            return "Unknown"
        
        with open(self.dhcpcd_conf, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.strip().startswith(f"interface {self.interface}"):
                return "Static"
        return "DHCP"

    def show_current_network_info(self):
        ip_address = self.get_current_ip()
        dhcp_state = self.get_dhcp_state()
        gateway = self.get_current_gateway()
        dns_servers = self.get_current_dns()
        
        print(f"Interface: {self.interface}")
        print(f"IP Address: {ip_address}")
        print(f"DHCP State: {dhcp_state}")
        print(f"Gateway: {gateway}")
        print(f"DNS Servers: {', '.join(dns_servers)}")