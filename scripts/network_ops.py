#!/usr/bin/env python3
"""
Network automation script for CI/CD pipeline
"""
import json
import os
import sys
from netmiko import ConnectHandler

def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

def connect_to_switch(device_info):
    """Establish SSH connection to switch"""
    try:
        connection = ConnectHandler(**device_info)
        print(" Successfully connected to switch")
        return connection
    except Exception as e:
        print(f" Connection failed: {str(e)}")
        sys.exit(1)

def create_vlans(connection, vlans):
    """Create VLANs on the switch"""
    commands = []
    for vlan in vlans:
        commands.append(f"vlan {vlan['id']}")
        commands.append(f"name {vlan['name']}")
    
    if commands:
        print("..... Creating VLANs...")
        output = connection.send_config_set(commands)
        print(output)
        return True
    return False

def configure_interfaces(connection, interfaces):
    """Configure switch interfaces"""
    for interface in interfaces:
        commands = [f"interface {interface['interface']}"]
        
        if 'mode' in interface:
            commands.append(f"switchport mode {interface['mode']}")
        
        if 'vlan' in interface and interface['mode'] == 'access':
            commands.append(f"switchport access vlan {interface['vlan']}")
        
        if 'description' in interface:
            commands.append(f"description {interface['description']}")
        
        commands.append("no shutdown")
        
        print(f"...........configuring {interface['interface']}...")
        output = connection.send_config_set(commands)
        print(output)

def save_config(connection):
    """Save the configuration"""
    print(".......saving configuration...")
    output = connection.send_command("write memory")
    print(output)

def main():
    # Get device info from environment variables (GitHub Secrets)
    device_info = {
        'device_type': 'cisco_ios',
        'host': os.getenv('SWITCH_IP'),
        'username': os.getenv('SWITCH_USERNAME'),
        'password': os.getenv('SWITCH_PASSWORD'),
        'secret': os.getenv('SWITCH_ENABLE_PASSWORD'),
        'port': 22,
    }
    
    # Validate required environment variables
    required_vars = ['SWITCH_IP', 'SWITCH_USERNAME', 'SWITCH_PASSWORD', 'SWITCH_ENABLE_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    print(f"Target Switch: {device_info['host']}")
    
    # Load configurations
    vlan_config = load_config('configs/vlan_config.json')
    network_config = load_config('configs/network_config.json')
    
    print(f"Configuration: {len(vlan_config['vlans'])} VLANs, {len(vlan_config['interfaces'])} interfaces")
    
    # Connect to switch
    connection = connect_to_switch(device_info)
    
    try:
        # Enter enable mode
        connection.enable()
        
        # Show current VLAN status
        print("Current VLAN configuration:")
        vlan_output = connection.send_command("show vlan brief")
        print(vlan_output)
        
        # Create VLANs
        create_vlans(connection, vlan_config['vlans'])
        
        # Configure interfaces
        configure_interfaces(connection, vlan_config['interfaces'])
        
        # Save configuration
        save_config(connection)
        
        # Show final status
        print("Configuration completed successfully!")
        print("Final VLAN configuration:")
        final_output = connection.send_command("show vlan brief")
        print(final_output)
        
    except Exception as e:
        print(f"Error during configuration: {str(e)}")
        sys.exit(1)
    finally:
        connection.disconnect()

if __name__ == "__main__":
    main()