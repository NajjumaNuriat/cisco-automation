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
        print(f" Error loading config: {e}")
        sys.exit(1)

def connect_to_iosxr(device_info):
    """Establish SSH connection to IOS XR sandbox"""
    try:
        # IOS XR specific connection parameters for sandbox
        device_info['global_delay_factor'] = 2
        device_info['timeout'] = 30
        device_info['session_timeout'] = 60
        
        print(f" Connecting to {device_info['host']}:{device_info['port']}...")
        connection = ConnectHandler(**device_info)
        print(" Successfully connected to IOS XR sandbox")
        return connection
    except Exception as e:
        print(f" IOS XR connection failed: {str(e)}")
        print("\n Troubleshooting tips:")
        print("   1. Check if sandbox-iosxr-1.cisco.com is accessible")
        print("   2. Verify credentials: admin/C1sco12345")
        print("   3. Ensure your network can reach Cisco DevNet")
        sys.exit(1)

def cleanup_existing_configs(connection):
    """Clean up existing subinterface configurations"""
    print("\n Cleaning up existing subinterfaces...")
    
    # List of subinterfaces to remove (including new ones)
    subinterfaces_to_remove = [
        "GigabitEthernet0/0/0/0.100",
        "GigabitEthernet0/0/0/0.400", 
        "GigabitEthernet0/0/0/1.200",
        "GigabitEthernet0/0/0/2.300",
        "GigabitEthernet0/0/0/0.10",
        "GigabitEthernet0/0/0/1.20",
        "GigabitEthernet0/0/0/2.30",
        "GigabitEthernet0/0/0/3.40"
    ]
    
    # Also remove OSPF configuration
    try:
        commands = ["no router ospf 1"]
        output = connection.send_config_set(commands)
        commit_output = connection.send_command("commit", expect_string=r"#")
        print("    Removed OSPF configuration")
    except:
        print("    No OSPF configuration to remove")
    
    for subif in subinterfaces_to_remove:
        try:
            commands = [f"no interface {subif}"]
            output = connection.send_config_set(commands)
            commit_output = connection.send_command("commit", expect_string=r"#")
            print(f"    Removed {subif}")
        except Exception as e:
            print(f"    Could not remove {subif}: {e}")

def configure_subinterfaces(connection, subinterfaces):
    """Configure VLAN subinterfaces on IOS XR"""
    print(" Configuring VLAN subinterfaces...")
    
    # Track which interfaces we've configured to avoid duplicates
    configured_interfaces = set()
    
    for subif in subinterfaces:
        if subif['subinterface'] in configured_interfaces:
            print(f"     Skipping duplicate: {subif['subinterface']}")
            continue
            
        commands = [
            f"interface {subif['parent_interface']}",
            "no shutdown",
            f"interface {subif['subinterface']}",
            f"description {subif['description']}",
            f"encapsulation dot1q {subif['vlan_id']}",
            f"ipv4 address {subif['ip_address']} {subif['subnet_mask']}",
            "no shutdown"
        ]
        
        print(f" Configuring {subif['subinterface']} for VLAN {subif['vlan_id']}...")
        
        try:
            # Send configuration commands
            output = connection.send_config_set(commands)
            
            # Commit configuration (IOS XR specific)
            commit_output = connection.send_command("commit", expect_string=r"#")
            print(f"    {subif['subinterface']} configured and committed")
            configured_interfaces.add(subif['subinterface'])
            
        except Exception as e:
            print(f" Error configuring {subif['subinterface']}: {e}")

def configure_static_routes(connection, routes):
    """Configure static routes on IOS XR"""
    if not routes:
        return
        
    print("  Configuring static routes...")
    
    try:
        commands = ["router static", "address-family ipv4 unicast"]
        
        for route in routes:
            route_cmd = f"{route['network']} {route['mask']} {route.get('next_hop', 'Null0')}"
            commands.append(route_cmd)
        
        # Send commands with proper expect string
        output = connection.send_config_set(commands)
        commit_output = connection.send_command("commit", expect_string=r"#")
        print("    Static routes configured and committed")
    except Exception as e:
        print(f"  Static routes configuration: {e}")
        # Continue execution even if routes fail

def configure_routing_protocols(connection, routing_configs):
    """Configure routing protocols on IOS XR"""
    if not routing_configs:
        return
        
    for routing_config in routing_configs:
        if routing_config['protocol'].lower() == 'ospf':
            print(f" Configuring OSPF Process {routing_config['process_id']}...")
            
            try:
                # Enter OSPF configuration mode
                commands = [f"router ospf {routing_config['process_id']}"]
                
                # Add network statements
                for network in routing_config['networks']:
                    network_cmd = f"area {network['area']} range {network['network']}"
                    commands.append(f"network {network['network']} {network['wildcard']} area {network['area']}")
                
                # Send OSPF configuration
                output = connection.send_config_set(commands)
                commit_output = connection.send_command("commit", expect_string=r"#")
                print(f"    OSPF Process {routing_config['process_id']} configured and committed")
                
            except Exception as e:
                print(f" Error configuring OSPF: {e}")

def verify_iosxr_configuration(connection):
    """Verify IOS XR configuration with proper commands"""
    print("\n Verifying IOS XR Configuration...")
    
    try:
        # 1. Show interface status
        print("\n Interface Status:")
        try:
            interfaces_output = connection.send_command("show interfaces brief", expect_string=r"#")
            print(interfaces_output)
        except:
            interfaces_output = connection.send_command("show interfaces brief")
            print(interfaces_output)
        
        # 2. Show our specific subinterfaces
        print("\n Our Configured Subinterfaces:")
        try:
            config_output = connection.send_command("show running-config interface", expect_string=r"#")
        except:
            config_output = connection.send_command("show running-config interface")
        
        # Check if our subinterfaces exist in the config
        our_subinterfaces = [
            "GigabitEthernet0/0/0/0.10",
            "GigabitEthernet0/0/0/1.20", 
            "GigabitEthernet0/0/0/2.30",
            "GigabitEthernet0/0/0/3.40"
        ]
        
        for subif in our_subinterfaces:
            if subif in config_output:
                print(f"    {subif} - Found in configuration")
            else:
                print(f"    {subif} - NOT found in configuration")
        
        # 3. Show IP addresses
        print("\n IP Address Assignment:")
        try:
            ip_output = connection.send_command("show ipv4 interface brief", expect_string=r"#")
            print(ip_output)
        except:
            ip_output = connection.send_command("show ipv4 interface brief")
            print(ip_output)
        
        # 4. Show OSPF status
        print("\n OSPF Routing Status:")
        try:
            ospf_output = connection.send_command("show ospf interface brief", expect_string=r"#")
            print(ospf_output)
        except:
            print("     OSPF not configured or cannot retrieve status")
        
        # 5. Show routes
        print("\n  Routing Table:")
        try:
            routes_output = connection.send_command("show route ipv4", expect_string=r"#")
            # Show only OSPF and connected routes
            for line in routes_output.split('\n'):
                if "OSPF" in line or "Connected" in line or "10.10." in line:
                    print(f"   {line}")
        except:
            routes_output = connection.send_command("show route ipv4")
            for line in routes_output.split('\n'):
                if "OSPF" in line or "Connected" in line or "10.10." in line:
                    print(f"   {line}")
        
    except Exception as e:
        print(f"Verification failed: {e}")

def save_iosxr_config(connection):
    """Save configuration on IOS XR"""
    print(" Saving IOS XR configuration...")
    try:
        # IOS XR uses different save command
        save_output = connection.send_command("commit", expect_string=r"#")
        print("    Configuration committed (changes applied)")
        
        # Try to save to startup (may not work in sandbox)
        try:
            save_output = connection.send_command("admin save running-config startup-config", expect_string=r"#")
            if "successful" in save_output.lower() or "[ok]" in save_output.lower():
                print("   Configuration saved to startup")
            else:
                print("    Configuration may not persist after sandbox reset")
        except:
            print("    Cannot save to startup in sandbox (normal for shared environment)")
            
    except Exception as e:
        print(f"    Save operation note: {e}")

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
    
    print(" Starting IOS XRv9000 Sandbox Automation")
    print("="*60)
    print(" Target: sandbox-iosxr-1.cisco.com (Cisco DevNet)")
    print(" Note: This is a SHARED sandbox - be respectful!")
    print("="*60)
    
    # Load configurations
    vlan_config = load_config('../configs/vlan_config.json')
    network_config = load_config('../configs/network_config.json')
    
    print(f" Configuration: {len(vlan_config['subinterfaces'])} subinterfaces, {len(vlan_config.get('routing_protocols', []))} routing protocols")
    
    # Connect to IOS XR sandbox
    connection = connect_to_iosxr(device_info)
    
    try:
        # Enter enable mode
        connection.enable()
        
        # Optional: Clean up existing configs first
        cleanup_existing_configs(connection)
        
        # Show initial configuration (simplified to avoid errors)
        print("\n Initial Sandbox State:")
        try:
            initial_interfaces = connection.send_command("show interfaces brief", expect_string=r"#")
            print("Existing interfaces:")
            print(initial_interfaces)
        except:
            print("  Could not retrieve initial interface state (continuing...)")
        
        # Configure subinterfaces
        configure_subinterfaces(connection, vlan_config['subinterfaces'])
        
        # Configure routing protocols
        if 'routing_protocols' in vlan_config:
            configure_routing_protocols(connection, vlan_config['routing_protocols'])
        
        # Verify configuration
        verify_iosxr_configuration(connection)
        
        # Try to save configuration
        save_iosxr_config(connection)
        
        print("\n" + "="*60)
        print(" IOS XRv9000 Sandbox Configuration Completed!")
        print("="*60)
        
    except Exception as e:
        print(f" Error during configuration: {str(e)}")
        sys.exit(1)
    finally:
        connection.disconnect()
        print("\n🔌 Disconnected from IOS XR sandbox")

if __name__ == "__main__":
    main()