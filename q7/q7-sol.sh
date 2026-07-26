# # LXD via snap (WSL2 Ubuntu works)
# sudo snap install lxd && sudo lxd init --auto

# # unprivileged container with a hard memory cap, 1 CPU, no host mounts
# lxc launch ubuntu:22.04 sandbox
# lxc config set sandbox limits.memory 512MB
# lxc config set sandbox limits.memory.enforce hard
# lxc config set sandbox limits.cpu 1

# # kill its networking so the net probe fails
# lxc config device add sandbox eth0 none

# # copy the script in and run it, capturing stdout+stderr together
# lxc file push probe.sh sandbox/root/probe.sh
# lxc exec sandbox -- bash -lc 'bash /root/probe.sh 2>&1'


# Install and initialize
sudo snap install lxd
sudo lxd init --auto

# Create the required host canary
sudo mkdir -p /tmp/tds-lxd-canary
echo 'TDS_LXD_CANARY_cfa2c4db63b29b2bf1f07346c57b5d7664433351' \
| sudo tee /tmp/tds-lxd-canary/c8df645005d0.txt

# Launch container
lxc launch ubuntu:22.04 sandbox

# Apply limits
lxc config set sandbox limits.memory 512MB
lxc config set sandbox limits.memory.enforce hard
lxc config set sandbox limits.cpu 1

# Remove networking
lxc stop sandbox
lxc config device remove sandbox eth0
lxc start sandbox

# Push probe
lxc file push probe.sh sandbox/root/probe.sh

# Run and capture combined stdout+stderr
lxc exec sandbox -- bash -lc \
'bash /root/probe.sh > /root/sandbox.log 2>&1'

# Retrieve log
lxc file pull sandbox/root/sandbox.log .
cat sandbox.log