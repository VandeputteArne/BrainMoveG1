cat << 'EOF' > start_frontend.sh
#!/bin/bash
sudo systemctl start brainmove-frontend.service
echo "Frontend gestart."
EOF