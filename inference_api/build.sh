#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e


# NOTE: This script is intended to be run as EC2 User Data, which executes as the 'root' user.
# Therefore, 'sudo' is not strictly necessary for the commands below, but it's kept for clarity
# and so the script can be easily adapted to run in other environments.

cd /root/

# 1. Update package lists and install dependencies
# Combined update, upgrade, and installation of all necessary packages in one go.
# Added 'git' which was missing.
apt-get update -y
apt-get upgrade -y
apt-get install -y ca-certificates curl gnupg lsb-release git

# 2. Add Docker's official GPG key and set up the repository
# This part is mostly unchanged but ensures directories exist before use.
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

# 3. Install Docker Engine
# Update package list again to include the new Docker repo, then install.
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# The Docker service is automatically started and enabled on install with modern packages,
# but we can be explicit just in case.
systemctl start docker
systemctl enable docker

#clone the repo

git clone https://github.com/andresmg42/MLAPI.git

cd MLAPI

git switch join

cd inferenceapi

# Build and run the containers.
# NOTE: Using 'docker compose' (with a space) which is the command for the v2 plugin.
# The '-d' flag is CRITICAL to run the containers in detached (background) mode,
# allowing the startup script to complete.
# The 'usermod' command has been removed as it is ineffective and unnecessary here.
docker compose build
docker compose up -d