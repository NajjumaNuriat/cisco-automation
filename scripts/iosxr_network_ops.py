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
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

def connect_to_iosxr(device_info):
    """Establish SSH connection to IOS XR sandbox"""
    try:
        # IOS XR specific connection parameters for sandbox
        device_info['global_delay_factor'] = 2
        device_info['timeout'] = 30
        device_info['session_timeout'] = 60
        
        print(f"🔗 Connecting to {device_info['host']}:{device_info['port']}...")
        connection = ConnectHandler(**device_info)
        print("✅ Successfully connected to IOS XR sandbox")
        return connection
    except Exception as e:
        print(f"❌ IOS XR connection failed: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Check if sandbox-iosxr-1.cisco.com is accessible")
        print("   2. Verify credentials: admin/C1sco12345")
        print("   3. Ensure your network can reach Cisco DevNet")
        sys.exit(1)

def cleanup_existing_configs(connection):
    """Clean up existing subinterface configurations"""
    print("\n🧹 Cleaning up existing subinterfaces...")
    
    # List of subinterfaces to remove
    subinterfaces_to_remove = [
        "GigabitEthernet0/0/0/0.100",
        "GigabitEthernet0/0/0/0.400", 
        "GigabitEthernet0/0/0/1.200",
        "GigabitEthernet0/0/0/2.300"
    ]
    
    for subif in subinterfaces_to_remove:
        try:
            commands = [f"no interface {subif}"]
            output = connection.send_config_set(commands)
            commit_output = connection.send_command("commit", expect_string=r"#")
            print(f"   ✅ Removed {subif}")
        except Exception as e:
            print(f"   ℹ️  Could not remove {subif}: {e}")

def configure_subinterfaces(connection, subinterfaces):
    """Configure VLAN subinterfaces on IOS XR"""
    print("🔄 Configuring VLAN subinterfaces...")
    
    # Track which interfaces we've configured to avoid duplicates
    configured_interfaces = set()
    
    for subif in subinterfaces:
        if subif['subinterface'] in configured_interfaces:
            print(f"   ⚠️  Skipping duplicate: {subif['subinterface']}")
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
        
        print(f"🔧 Configuring {subif['subinterface']} for VLAN {subif['vlan_id']}...")
        
        try:
            # Send configuration commands
            output = connection.send_config_set(commands)
            
            # Commit configuration (IOS XR specific)
            commit_output = connection.send_command("commit", expect_string=r"#")
            print(f"   ✅ {subif['subinterface']} configured and committed")
            configured_interfaces.add(subif['subinterface'])
            
        except Exception as e:
            print(f"❌ Error configuring {subif['subinterface']}: {e}")

def configure_static_routes(connection, routes):
    """Configure static routes on IOS XR"""
    if not routes:
        return
        
    print("🛣️  Configuring static routes...")
    
    try:
        commands = ["router static", "address-family ipv4 unicast"]
        
        for route in routes:
            route_cmd = f"{route['network']} {route['mask']} {route.get('next_hop', 'Null0')}"
            commands.append(route_cmd)
        
        # Send commands with proper expect string
        output = connection.send_config_set(commands)
        commit_output = connection.send_command("commit", expect_string=r"#")
        print("   ✅ Static routes configured and committed")
    except Exception as e:
        print(f"⚠️  Static routes configuration: {e}")
        # Continue execution even if routes fail

def verify_iosxr_configuration(connection):
    """Verify IOS XR configuration with proper commands"""
    print("\n🔍 Verifying IOS XR Configuration...")
    
    try:
        # 1. Show interface status (correct IOS XR command)
        print("\n📡 Interface Status:")
        try:
            interfaces_output = connection.send_command("show interfaces brief", expect_string=r"#")
            print(interfaces_output)
        except:
            interfaces_output = connection.send_command("show interfaces brief")
            print(interfaces_output)
        
        # 2. Show our specific subinterfaces
        print("\n✅ Our Configured Subinterfaces:")
        try:
            config_output = connection.send_command("show running-config interface", expect_string=r"#")
        except:
            config_output = connection.send_command("show running-config interface")
        
        # Check if our subinterfaces exist in the config
        our_subinterfaces = [
            "GigabitEthernet0/0/0/0.100",
            "GigabitEthernet0/0/0/1.200", 
            "GigabitEthernet0/0/0/2.300"
        ]
        
        for subif in our_subinterfaces:
            if subif in config_output:
                print(f"   ✅ {subif} - Found in configuration")
            else:
                print(f"   ❌ {subif} - NOT found in configuration")
        
        # 3. Show IP addresses (correct IOS XR command)
        print("\n🌐 IP Address Assignment:")
        try:
            ip_output = connection.send_command("show ipv4 interface brief", expect_string=r"#")
            print(ip_output)
        except:
            ip_output = connection.send_command("show ipv4 interface brief")
            print(ip_output)
        
        # 4. Show routes (correct IOS XR command)
        print("\n🛣️  IPv4 Routing Table (Our Networks):")
        try:
            routes_output = connection.send_command("show route ipv4", expect_string=r"#")
        except:
            routes_output = connection.send_command("show route ipv4")
        
        # Filter to show only our configured networks
        for line in routes_output.split('\n'):
            if any(network in line for network in ['192.168.10', '192.168.20', '192.168.30', '192.168.100', '192.168.200']):
                print(f"   {line}")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

def save_iosxr_config(connection):
    """Save configuration on IOS XR"""
    print("💾 Saving IOS XR configuration...")
    try:
        # IOS XR uses different save command
        save_output = connection.send_command("commit", expect_string=r"#")
        print("   ✅ Configuration committed (changes applied)")
        
        # Try to save to startup (may not work in sandbox)
        try:
            save_output = connection.send_command("admin save running-config startup-config", expect_string=r"#")
            if "successful" in save_output.lower() or "[ok]" in save_output.lower():
                print("   ✅ Configuration saved to startup")
            else:
                print("   ℹ️  Configuration may not persist after sandbox reset")
        except:
            print("   ℹ️  Cannot save to startup in sandbox (normal for shared environment)")
            
    except Exception as e:
        print(f"   ℹ️  Save operation note: {e}")

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
    
    print("🚀 Starting IOS XRv9000 Sandbox Automation")
    print("="*60)
    print("🎯 Target: sandbox-iosxr-1.cisco.com (Cisco DevNet)")
    print("📝 Note: This is a SHARED sandbox - be respectful!")
    print("="*60)
    
    # Load configurations
    vlan_config = load_config('../configs/vlan_config.json')
    network_config = load_config('../configs/network_config.json')
    
    print(f"📁 Configuration: {len(vlan_config['subinterfaces'])} subinterfaces, {len(vlan_config.get('static_routes', []))} routes")
    
    # Connect to IOS XR sandbox
    connection = connect_to_iosxr(device_info)
    
    try:
        # Enter enable mode
        connection.enable()
        
        # Optional: Clean up existing configs first
        cleanup_existing_configs(connection)
        
        # Show initial configuration (simplified to avoid errors)
        print("\n📋 Initial Sandbox State:")
        try:
            initial_interfaces = connection.send_command("show interfaces brief", expect_string=r"#")
            print("Existing interfaces:")
            print(initial_interfaces)
        except:
            print("   ℹ️  Could not retrieve initial interface state (continuing...)")
        
        # Configure subinterfaces
        configure_subinterfaces(connection, vlan_config['subinterfaces'])
        
        # Configure static routes
        configure_static_routes(connection, vlan_config.get('static_routes', []))
        
        # Verify configuration
        verify_iosxr_configuration(connection)
        
        # Try to save configuration
        save_iosxr_config(connection)
        
        print("\n" + "="*60)
        print("✅ IOS XRv9000 Sandbox Configuration Completed!")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error during configuration: {str(e)}")
        sys.exit(1)
    finally:
        connection.disconnect()
        print("\n🔌 Disconnected from IOS XR sandbox")

if __name__ == "__main__":
    main()