#!/usr/bin/env python3
"""
Simple network automation script for VLAN and interface configuration
Updated for Core-Switch-1 (192.168.2.129)
"""

import json
import os
from netmiko import ConnectHandler
import sys

def load_config(config_file):
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Config file {config_file} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON format")
        sys.exit(1)

def connect_to_switch(device_info):
    """Establish SSH connection to switch"""
    try:
        connection = ConnectHandler(**device_info)
        print("Successfully connected to switch")
        return connection
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        sys.exit(1)

def create_vlans(connection, vlans):
    """Create VLANs on the switch"""
    commands = []
    for vlan in vlans:
        commands.append(f"vlan {vlan['id']}")
        commands.append(f"name {vlan['name']}")
    
    if commands:
        print("Creating VLANs...")
        output = connection.send_config_set(commands)
        print(output)
        return True
    return False

def update_interface_descriptions(connection, interfaces):
    """Update interface descriptions"""
    for interface in interfaces:
        commands = [
            f"interface {interface['interface']}",
            f"description {interface['description']}"
        ]
        print(f"Configuring {interface['interface']}...")
        output = connection.send_config_set(commands)
        print(output)

def save_config(connection):
    """Save the configuration"""
    print("Saving configuration...")
    output = connection.send_command("write memory")
    print(output)

def show_current_vlans(connection):
    """Display current VLAN configuration"""
    print("Current VLAN configuration:")
    output = connection.send_command("show vlan brief")
    print(output)

def show_interface_status(connection):
    """Display interface descriptions"""
    print("Current interface status:")
    output = connection.send_command("show interfaces description")
    print(output)

def main():
    # Device connection parameters for Core-Switch-1
    device = {
        'device_type': 'cisco_ios',
        'host': os.getenv('SWITCH_IP', '192.168.2.129'),  # Updated IP
        'username': os.getenv('SWITCH_USERNAME', 'admin'),
        'password': os.getenv('SWITCH_PASSWORD', 'cisco'),  # Updated password
        'secret': os.getenv('SWITCH_ENABLE_PASSWORD', 'cisco'),  # Updated enable secret
        'port': 22,
    }
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), '../configs/vlan_config.json')
    config = load_config(config_path)
    
    # Connect to switch
    connection = connect_to_switch(device)
    
    try:
        # Enter enable mode
        connection.enable()
        
        # Show current configuration
        print("\n" + "="*50)
        show_current_vlans(connection)
        show_interface_status(connection)
        print("="*50 + "\n")
        
        # Create VLANs
        if 'vlans' in config:
            create_vlans(connection, config['vlans'])
        
        # Update interface descriptions
        if 'interfaces' in config:
            update_interface_descriptions(connection, config['interfaces'])
        
        # Save configuration
        save_config(connection)
        
        # Show configuration after changes
        print("\n" + "="*50)
        print("Configuration after changes:")
        show_current_vlans(connection)
        show_interface_status(connection)
        print("="*50 + "\n")
        
        print("Configuration completed successfully!")
        
    except Exception as e:
        print(f"Error during configuration: {str(e)}")
        sys.exit(1)
    finally:
        connection.disconnect()

if __name__ == "__main__":
    main()