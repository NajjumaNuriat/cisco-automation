#!/usr/bin/env python3
"""
IOS XR Network Automation for XRv9000 Sandbox
Target: sandbox-iosxr-1.cisco.com
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

def connect_to_iosxr(device_info):
    """Establish SSH connection to IOS XR sandbox"""
    try:
        # IOS XR specific connection parameters for sandbox
        device_info['global_delay_factor'] = 2
        device_info['timeout'] = 30
        device_info['session_timeout'] = 60
        
        print(f".......onnecting to {device_info['host']}:{device_info['port']}...")
        connection = ConnectHandler(**device_info)
        print("Successfully connected to IOS XR sandbox")
        return connection
    except Exception as e:
        print(f"IOS XR connection failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("   1. Check if sandbox-iosxr-1.cisco.com is accessible")
        print("   2. Verify credentials: admin/C1sco12345")
        print("   3. Ensure your network can reach Cisco DevNet")
        sys.exit(1)

def configure_subinterfaces(connection, subinterfaces):
    """Configure VLAN subinterfaces on IOS XR"""
    print("Configuring VLAN subinterfaces...")
    
    for subif in subinterfaces:
        commands = [
            f"interface {subif['parent_interface']}",
            "no shutdown",
            f"interface {subif['subinterface']}",
            f"description {subif['description']}",
            f"encapsulation dot1q {subif['vlan_id']}",
            f"ipv4 address {subif['ip_address']} {subif['subnet_mask']}",
            "no shutdown"
        ]
        
        print(f"Configuring {subif['subinterface']} for VLAN {subif['vlan_id']}...")
        
        try:
            # Send configuration commands
            output = connection.send_config_set(commands)
            
            # Commit configuration (IOS XR specific)
            commit_output = connection.send_command("commit", expect_string=r"#")
            print(f" {subif['subinterface']} configured and committed")
            
        except Exception as e:
            print(f"Error configuring {subif['subinterface']}: {e}")

def configure_static_routes(connection, routes):
    """Configure static routes on IOS XR"""
    if not routes:
        return
        
    print("Configuring static routes...")
    
    commands = ["router static", "address-family ipv4 unicast"]
    
    for route in routes:
        route_cmd = f"{route['network']} {route['mask']} {route.get('next_hop', 'Null0')}"
        commands.append(route_cmd)
    
    try:
        output = connection.send_config_set(commands)
        commit_output = connection.send_command("commit", expect_string=r"#")
        print(" Static routes configured and committed")
    except Exception as e:
        print(f" Error configuring static routes: {e}")
def verify_iosxr_configuration(connection):
    """Verify IOS XR configuration with proper command syntax"""
    print("\n....Verifying IOS XR Configuration...")
    
    try:
        # Show interfaces brief (correct command for IOS XR)
        print("\n Interface Status:")
        interfaces_output = connection.send_command("show interfaces brief")
        print(interfaces_output)
        
        # Show subinterfaces - use different approach for IOS XR
        print("\n Subinterface Details:")
        try:
            # Method 1: Show all interfaces and filter in Python
            all_interfaces = connection.send_command("show interfaces description")
            print("All Interfaces:")
            print(all_interfaces)
        except:
            # Method 2: Use IOS XR specific filtering
            subif_output = connection.send_command("show interfaces | include \"\\.[0-9]\"")
            print("Subinterfaces found:")
            print(subif_output if subif_output else "No subinterfaces found")
        
        # Show routes (correct command for IOS XR)
        print("\n IPv4 Routing Table:")
        routes_output = connection.send_command("show route ipv4")
        # Show only our configured routes to avoid too much output
        for line in routes_output.split('\n'):
            if "192.168" in line or "connected" in line.lower():
                print(f"   {line}")
        
        # Show running config for subinterfaces (simplified)
        print("\nSubinterface Configuration:")
        config_output = connection.send_command("show running-config interface")
        # Extract just the relevant parts
        lines = config_output.split('\n')
        in_subinterface = False
        for line in lines:
            if line.strip().startswith('interface') and '.' in line:
                in_subinterface = True
                print(line)
            elif line.strip().startswith('interface') and not '.' in line:
                in_subinterface = False
            elif in_subinterface and line.strip() and not line.strip().startswith('!'):
                print(f"   {line}")
        
    except Exception as e:
        print(f"Verification failed: {e}")
def save_iosxr_config(connection):
    """Save configuration on IOS XR"""
    print("💾 Saving IOS XR configuration...")
    try:
        # IOS XR uses different save command
        save_output = connection.send_command("commit", expect_string=r"#")
        print(" Configuration committed (changes applied)")
        
        # Try to save to startup (may not work in sandbox)
        try:
            save_output = connection.send_command("admin save running-config startup-config", expect_string=r"#")
            if "successful" in save_output.lower() or "[ok]" in save_output.lower():
                print(" Configuration saved to startup")
            else:
                print(" Configuration may not persist after sandbox reset")
        except:
            print(" Cannot save to startup in sandbox (normal for shared environment)")
            
    except Exception as e:
        print(f" Save operation note: {e}")        
        
def cleanup_configuration(connection):
    """Optional: Clean up configuration (for shared sandbox)"""
    print("\nCleaning up configuration (respecting shared sandbox)...")
    try:
        # Remove our subinterfaces
        commands = [
            "no interface GigabitEthernet0/0/0/0.100",
            "no interface GigabitEthernet0/0/0/1.200", 
            "no interface GigabitEthernet0/0/0/2.300",
            "no router static"
        ]
        output = connection.send_config_set(commands)
        commit_output = connection.send_command("commit")
        print(" Configuration cleaned up")
    except Exception as e:
        print(f"Cleanup not required: {e}")

def main():
    # IOS XR sandbox connection parameters
    device_info = {
        'device_type': 'cisco_xr',
        'host': os.getenv('SWITCH_IP', 'sandbox-iosxr-1.cisco.com'),
        'username': os.getenv('SWITCH_USERNAME', 'admin'),
        'password': os.getenv('SWITCH_PASSWORD', 'C1sco12345'),
        'secret': os.getenv('SWITCH_ENABLE_PASSWORD', 'C1sco12345'),
        'port': int(os.getenv('SWITCH_PORT', 22)),
    }
    
    print("..........Starting IOS XRv9000 Sandbox Automation..........")
    print("="*60)
    print("Target: sandbox-iosxr-1.cisco.com (Cisco DevNet)")
    print("Note: This is a SHARED sandbox - be respectful!")
    print("="*60)
    
    # Load configurations
    vlan_config = load_config('../configs/vlan_config.json')
    network_config = load_config('../configs/network_config.json')
    
    print(f"Configuration: {len(vlan_config['subinterfaces'])} subinterfaces, {len(vlan_config.get('static_routes', []))} routes")
    
    # Connect to IOS XR sandbox
    connection = connect_to_iosxr(device_info)
    
    try:
        # Enter enable mode
        connection.enable()
        
        # Show initial configuration
        print("\nInitial Sandbox State:")
        initial_interfaces = connection.send_command("show interfaces description | include \\.")
        print("Existing subinterfaces:", initial_interfaces if initial_interfaces else "None")
        
        # Configure subinterfaces
        configure_subinterfaces(connection, vlan_config['subinterfaces'])
        
        # Configure static routes
        configure_static_routes(connection, vlan_config.get('static_routes', []))
        
        # Verify configuration
        verify_iosxr_configuration(connection)
        
        # Try to save configuration
        save_iosxr_config(connection)
        
        print("\n" + "="*60)
        print(" IOS XRv9000 Sandbox Configuration Completed!")
        print("="*60)
        
        # Ask about cleanup (for shared sandbox)
        if os.getenv('CLEANUP', 'false').lower() == 'true':
            cleanup_configuration(connection)
        
    except Exception as e:
        print(f"Error during configuration: {str(e)}")
        sys.exit(1)
    finally:
        connection.disconnect()
        print("\n Disconnected from IOS XR sandbox")

if __name__ == "__main__":
    main()