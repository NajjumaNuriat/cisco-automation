# Cisco Network Automation

Simple Python automation for VLAN creation and interface description updates.

## Switch Configuration

- **Device**: Core-Switch-1
- **Management IP**: 192.168.2.129
- **Username**: admin
- **Password**: cisco
- **Enable Secret**: cisco

## Setup

1. Clone this repository
2. Configure GitHub Secrets:

   - SWITCH_IP: 192.168.2.129
   - SWITCH_USERNAME: admin
   - SWITCH_PASSWORD: cisco
   - SWITCH_ENABLE_PASSWORD: cisco

3. Update `configs/vlan_config.json` with your desired VLAN and interface configurations

## Usage

- Push to main branch to trigger syntax validation and dry run
- Use "Run workflow" in GitHub Actions for manual deployment
- The script will show before/after configuration states

## Current VLAN Structure

- VLAN 10: Management (pre-configured)
- VLAN 20: Users (pre-configured)
- VLAN 30: HR (pre-configured)
- VLAN 40: Finance (pre-configured)
- VLAN 50: IT (pre-configured)
