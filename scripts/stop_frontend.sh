cat << 'EOF' > stop_frontend.sh
#!/bin/bash
sudo systemctl stop brainmove-frontend.service
echo "Frontend gestopt."
EOF