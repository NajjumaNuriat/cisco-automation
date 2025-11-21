# Network Automation CI/CD

Automated VLAN and interface configuration using GitHub Actions.

## Setup

1. **Configure GitHub Secrets** in your repository:

   - `SWITCH_IP`: IP address of your network device
   - `SWITCH_USERNAME`: SSH username
   - `SWITCH_PASSWORD`: SSH password
   - `SWITCH_ENABLE_PASSWORD`: Enable password

2. **Update Configuration Files**:
   - `configs/network_config.json`: Network topology and device info
   - `configs/vlan_config.json`: VLANs and interfaces to configure

## Usage

### Continuous Integration (Automatic)

- Every push/PR validates configuration syntax
- Shows deployment plan without making changes

### Continuous Deployment (Manual)

- Go to GitHub Actions → "Network Configuration CI/CD"
- Click "Run workflow" to deploy changes
- Requires manual approval for safety

## Configuration

Edit `configs/vlan_config.json` to:

- Add/remove VLANs
- Configure interface descriptions
- Assign VLANs to ports

## Security

- Credentials stored in GitHub Secrets
- Manual deployment required
- Configuration validated before deployment
