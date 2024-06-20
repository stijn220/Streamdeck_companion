import os
import time
from network import PiNetwork

network = PiNetwork()

def display_ip_local():
    return 'local: ' + network.get_current_ip()


def display_ip_remote():
    return 'remote: ' +  '192.168.178.159'

def change_ip_local_dhcp():
    print("Change Local IP to DHCP")

def change_ip_local_address():
    print("Change Local IP Address")

def change_ip_remote_address():
    print("Change Remote IP Address")

def change_code():
    print("Change Code")

def restart_network():
    print("Restart Network")

def restart_companion():
    print("Restart Companion")

def restart_raspberry():
    print("Restart Raspberry")

functionHandlersDictionary = {
    "display_ip_local": display_ip_local,
    "display_ip_remote": display_ip_remote,
    "change_ip_local_dhcp": change_ip_local_dhcp,
    "change_ip_local_address": change_ip_local_address,
    "change_ip_remote_address": change_ip_remote_address,
    "change_code": change_code,
    "restart_network": restart_network,
    "restart_companion": restart_companion,
    "restart_raspberry": restart_raspberry,
}
