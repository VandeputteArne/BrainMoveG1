cat << 'EOF' > start_backend.sh
#!/bin/bash
sudo systemctl start brainmove-backend.service
echo "Backend gestart."
EOF