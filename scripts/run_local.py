#!/usr/bin/env python3
"""
Local execution script for Packet Tracer environment
"""
import os
import subprocess
import sys

def run_local():
    print("🚀 Starting Local Network Automation")
    print("="*50)
    
    # Validate configuration first
    try:
        print("🔍 Validating configuration...")
        result = subprocess.run([
            'python', '-m', 'json.tool', 'configs/vlan_config.json'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Configuration validation passed")
        else:
            print("❌ Configuration validation failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False
    
    # Run the network operations
    print("\n🎯 Deploying to local Packet Tracer switch...")
    try:
        # Set environment variables for local execution
        env = os.environ.copy()
        env.update({
            'SWITCH_IP': '192.168.2.129',
            'SWITCH_USERNAME': 'admin', 
            'SWITCH_PASSWORD': 'cisco',
            'SWITCH_ENABLE_PASSWORD': 'cisco'
        })
        
        result = subprocess.run([
            'python', 'network_ops.py'
        ], env=env, cwd='scripts', text=True)
        
        if result.returncode == 0:
            print("✅ Local deployment completed successfully!")
            return True
        else:
            print("❌ Local deployment failed")
            return False
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

if __name__ == "__main__":
    success = run_local()
    sys.exit(0 if success else 1)