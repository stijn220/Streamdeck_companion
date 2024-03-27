import mainv2

# Create an instance of MenuSystem
menu_system = mainv2.MenuSystem()

# Create an instance of NetworkManager directly
nm = mainv2.NetworkManager()

# Get IPv4 address using NetworkManager instance
ip = nm.get_ipv4()

# Get IPv4 address using NetworkManager instance from MenuSystem instance
ip2 = menu_system.network.get_ipv4()

print(menu_system.get_ipv4_placeholder())

# Print the IPv4 address and its type
print(ip2)
print(type(ip2))
 