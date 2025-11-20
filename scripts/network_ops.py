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
        # If relative path, make it absolute relative to this script
        if not os.path.isabs(config_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_file = os.path.join(script_dir, config_file)
            
        print(f"📁 Loading config from: {config_file}")
        
        with open(config_file, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"❌ Error: Config file {config_file} not found")
        # Show available files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"📂 Files in script directory ({script_dir}):")
        for file in os.listdir(script_dir):
            print(f"   - {file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format")
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

def test_connectivity(host):
    """Test if we can reach the switch"""
    import socket
    try:
        print(f"🔍 Testing connectivity to {host}...")
        socket.setdefaulttimeout(3)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, 22))
        sock.close()
        if result == 0:
            print("✅ Switch is reachable on port 22")
            return True
        else:
            print(f"❌ Cannot reach {host} on port 22")
            print("   Please check:")
            print("   1. Packet Tracer is running")
            print("   2. Switch IP is 192.168.2.129")
            print("   3. SSH is enabled on the switch")
            print("   4. Your PC can ping the switch in Packet Tracer")
            return False
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False

def main():
    # Device connection parameters for Core-Switch-1
    device = {
        'device_type': 'cisco_ios',
        'host': os.getenv('SWITCH_IP', '192.168.2.129'),
        'username': os.getenv('SWITCH_USERNAME', 'admin'),
        'password': os.getenv('SWITCH_PASSWORD', 'cisco'),
        'secret': os.getenv('SWITCH_ENABLE_PASSWORD', 'cisco'),
        'port': 22,
    }
    # Test connectivity first
    if not test_connectivity(device['host']):
        sys.exit(1)
    
    # Load configuration - use relative path that works from scripts directory
    config_path = '../configs/vlan_config.json'  # Go up one level from scripts/ to find configs/
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