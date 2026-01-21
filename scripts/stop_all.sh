cat << 'EOF' > stop_all.sh
#!/bin/bash
sudo systemctl stop brainmove-frontend.service
sudo systemctl stop brainmove-backend.service
echo "Alle services gestopt."
EOF