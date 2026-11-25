#!/bin/bash
set -e
echo "lucas.martin:Lyux2026!" | chpasswd
echo "emma.bernard:Lyux2026!" | chpasswd
echo "hugo.dubois:Lyux2026!" | chpasswd
echo "lea.thomas:Lyux2026!" | chpasswd
echo "thomas.durand:Lyux2026!" | chpasswd
echo "sophie.leroy:Lyux2026!" | chpasswd
echo "alain.direction:Lyux2026!" | chpasswd
echo "claire.viesco:Lyux2026!" | chpasswd
echo "admin.lyux:Lyux2026!" | chpasswd

# Débloquer si verrouillé
passwd -u lucas.martin 2>/dev/null || true

echo "Passwords set successfully on LyuX-Server."
