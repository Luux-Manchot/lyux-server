#!/bin/bash
set -e

for u in /srv/samba/homes/*; do
    if [ -d "$u" ]; then
        uname=$(basename "$u")
        grp=$(id -gn "$uname" 2>/dev/null || echo "eleves")
        echo "Fixing ownership for $uname:$grp on $u"
        chown -R "$uname:$grp" "$u"
        chmod 700 "$u"
        # S'assurer que les sous-dossiers et fichiers ont les bons droits
        chmod -R u+rwX "$u"
    fi
done

echo "All home permissions fixed successfully."
