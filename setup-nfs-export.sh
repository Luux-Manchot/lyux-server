#!/bin/bash
set -e
echo '/srv/samba/homes 192.168.10.0/24(rw,sync,no_subtree_check,no_root_squash)' > /etc/exports
exportfs -ra
systemctl restart nfs-server
echo "NFS exported successfully."
