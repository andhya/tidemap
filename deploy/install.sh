#!/bin/sh
# Run from ~/tidemap
set -e
cd "$HOME/tidemap"
mkdir -p "$HOME/.config/systemd/user"
cp deploy/tidemap.service deploy/tidemap-generate.service deploy/tidemap-generate.timer "$HOME/.config/systemd/user/"
loginctl enable-linger
systemctl --user daemon-reload
systemctl --user start tidemap-generate
systemctl --user enable --now tidemap tidemap-generate.timer
