import network

net = network.PiNetwork()
print("Before setting static IP:")
net.show_current_network_info()
# Set static IP address
net.set_static_ip(ip_address='192.168.178.60')
print("\nAfter setting static IP:")
net.show_current_network_info()
