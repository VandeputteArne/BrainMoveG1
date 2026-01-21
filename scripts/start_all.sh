cat << 'EOF' > start_all.sh
#!/bin/bash
sudo systemctl start brainmove-backend.service
sudo systemctl start brainmove-frontend.service
echo "Alle services gestart."
EOF