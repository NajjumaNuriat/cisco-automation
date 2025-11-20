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
    
    # Check if we can reach the switch first
    print("🔍 Testing switch connectivity...")
    
    # Change to scripts directory
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(scripts_dir)
    
    # Run the network operations
    print("🎯 Deploying to local Packet Tracer switch...")
    
    # Set environment variables
    env = os.environ.copy()
    env.update({
        'SWITCH_IP': '192.168.2.129',
        'SWITCH_USERNAME': 'admin', 
        'SWITCH_PASSWORD': 'cisco',
        'SWITCH_ENABLE_PASSWORD': 'cisco'
    })
    
    try:
        result = subprocess.run([
            'python', 'network_ops.py'
        ], env=env, text=True)
        
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