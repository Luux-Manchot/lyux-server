#!/bin/bash
set -e

for u in /srv/samba/homes/*; do
    if [ -d "$u" ]; then
        uname=$(basename "$u")
        mkdir -p "$u/Bureau" "$u/Documents" "$u/Téléchargements" "$u/Images" "$u/Musique" "$u/Vidéos"
        # Préserver le propriétaire
        chown "$uname" "$u/Bureau" "$u/Documents" "$u/Téléchargements" "$u/Images" "$u/Musique" "$u/Vidéos" 2>/dev/null || true
        chmod 700 "$u" 2>/dev/null || true
    fi
done

echo "XDG user folders initialized on LyuX-Server homes."
