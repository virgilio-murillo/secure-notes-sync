#!/usr/bin/env bash
# generate-setup.sh — Generate setup commands for a new device.
# Run this on a machine that already has nsync configured,
# or provide values interactively.
set -euo pipefail

CONFIG="$HOME/.config/nsync/config.json"
REPO_URL=$(git -C "$(dirname "$0")" remote get-url origin 2>/dev/null || echo "https://github.com/<your-user>/secure-notes-sync.git")

# Read from existing config or prompt
if [ -f "$CONFIG" ]; then
    echo "Reading from existing config: $CONFIG"
    read_cfg() { python3 -c "import json; print(json.load(open('$CONFIG'))['$1'])"; }
    REGION=$(read_cfg region)
    POOL_ID=$(read_cfg user_pool_id)
    CLIENT_ID=$(read_cfg client_id)
    IDENTITY_POOL_ID=$(read_cfg identity_pool_id)
    BUCKET=$(read_cfg bucket)
    USERNAME=$(read_cfg username)
    DEVICE_PWD=$(read_cfg device_password)
    CLOUD_KEY=$(read_cfg cloud_key)
else
    echo "No config found. Enter values from CDK deploy output:"
    read -rp "Region [us-east-1]: " REGION; REGION=${REGION:-us-east-1}
    read -rp "User Pool ID: " POOL_ID
    read -rp "Client ID: " CLIENT_ID
    read -rp "Identity Pool ID: " IDENTITY_POOL_ID
    read -rp "Bucket name: " BUCKET
    read -rp "Username: " USERNAME
    read -rp "Device password: " DEVICE_PWD
    read -rp "Cloud key: " CLOUD_KEY
fi

echo ""
read -rp "New device ID (e.g. arch-trusted, mac-work): " DEVICE_ID
read -rp "Trusted device? [y/N]: " TRUSTED_INPUT
[[ "${TRUSTED_INPUT,,}" == "y" ]] && TRUSTED=true || TRUSTED=false

cat << COMMANDS

#============================================================
# nsync setup commands for: $DEVICE_ID
# Generated on $(date -u +%Y-%m-%dT%H:%M:%SZ)
# Copy everything below and paste into the target device.
#============================================================

# 1. Clone and install
git clone $REPO_URL ~/secure-notes-sync
cd ~/secure-notes-sync/cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 2. Create config
mkdir -p ~/.config/nsync && chmod 700 ~/.config/nsync
cat > ~/.config/nsync/config.json << 'EOF'
{
  "region": "$REGION",
  "user_pool_id": "$POOL_ID",
  "client_id": "$CLIENT_ID",
  "identity_pool_id": "$IDENTITY_POOL_ID",
  "bucket": "$BUCKET",
  "username": "$USERNAME",
  "device_password": "$DEVICE_PWD",
  "cloud_key": "$CLOUD_KEY",
  "refresh_token": "",
  "device_id": "$DEVICE_ID",
  "trusted": $TRUSTED
}
EOF
chmod 600 ~/.config/nsync/config.json

# 3. First auth (enter TOTP from phone — only time ever)
nsync pull
COMMANDS

if [ "$TRUSTED" = "true" ]; then
cat << 'TRUSTED_CMDS'

# 4. Import existing pass store to cloud
nsync import-pass

# 5. Hook into pass (auto-sync on use)
echo 'source ~/secure-notes-sync/cli/pass-nsync.bash' >> ~/.bashrc
source ~/.bashrc

# 6. Review pending changes from untrusted devices
nsync approve
TRUSTED_CMDS
fi

echo ""
echo "#============================================================"
echo "# Done. After step 3, TOTP is never needed again on this device."
echo "#============================================================"
