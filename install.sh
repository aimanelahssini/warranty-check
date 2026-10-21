#!/usr/bin/env bash
# Install the `warranty` command and an app-grid launcher for the current user.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.local/bin ~/.local/share/applications
ln -sf "$DIR/warranty" ~/.local/bin/warranty
cat > ~/.local/share/applications/warranty-check.desktop <<DESK
[Desktop Entry]
Type=Application
Name=Warranty Check
Comment=Check laptop warranty by serial number
Exec=$HOME/.local/bin/warranty
Icon=security-high-symbolic
Categories=Utility;
DESK
echo "Installed. Run 'warranty' or open Warranty Check from the app grid."
