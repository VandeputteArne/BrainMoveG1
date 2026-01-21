cat << 'EOF' > restart_backend.sh
#!/bin/bash
sudo systemctl restart brainmove-backend.service
echo "Backend herstart."
EOF