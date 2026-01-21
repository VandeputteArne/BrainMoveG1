cat << 'EOF' > stop_backend.sh
#!/bin/bash
sudo systemctl stop brainmove-backend.service
echo "Backend gestopt."
EOF