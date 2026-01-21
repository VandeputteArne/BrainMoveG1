cat << 'EOF' > restart_all.sh
#!/bin/bash
sudo systemctl restart brainmove-backend.service
sudo systemctl restart brainmove-frontend.service
echo "Alle services herstart."
EOF