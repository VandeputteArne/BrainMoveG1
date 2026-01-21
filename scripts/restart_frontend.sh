cat << 'EOF' > restart_frontend.sh
#!/bin/bash
sudo systemctl restart brainmove-frontend.service
echo "Frontend herstart."
EOF