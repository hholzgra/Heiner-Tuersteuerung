#!/bin/bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Bashrc Aenderungen
## Add Screensaver Options
BASHRC_FILE="$HOME/.bashrc"
echo 'xset s 20' >> "$BASHRC_FILE"
echo 'xset dpms 20 20 20' >> "$BASHRC_FILE"
echo 'xset q' >> "$BASHRC_FILE"
## Custom command um piclone schnell starten zu koennen
echo -e "\nalias clonesdcard='sudo dbus-launch piclone'" >> "$BASHRC_FILE"

# Fuer blanken Bildschirm
AUTOSTART_FILE="$HOME/.config/lxsession/LXDE-pi/autostart"
echo '@xset s 0 0' >> "$AUTOSTART_FILE"
echo '@xset s noblank' >> "$AUTOSTART_FILE"
echo '@xset s noexpose' >> "$AUTOSTART_FILE"
echo '@xset dpms 0 0 20' >> "$AUTOSTART_FILE"
echo '@python /home/raspberry/system_services_tuer/tuer_klingel_GUI_mitRelais.py' >> "$AUTOSTART_FILE"

# Installation zusätzlicher Pakete eventuell nötig
pip install nfcpy tomli
sudo apt-get install -y python3-requests ython3-systemd python3-pil.imagetk

# System Services
SYSTEMD_FOLDER="/etc/systemd/system"
sudo cp "$SCRIPT_DIR"/tuer_gpio_backlight_control.service "$SYSTEMD_FOLDER"
sudo cp "$SCRIPT_DIR"/tuer_nfc_sensor.service "$SYSTEMD_FOLDER"

# Änderungen übernehmen / aktivieren
sudo systemctl daemon-reload

# Dienste starten
sudo systemctl enable --now tuer_gpio_backlight_control.service
sudo systemctl enable --now tuer_nfc_sensor.service


chmod +x "$SCRIPT_DIR"/../tuer_gpio_backlight_control.py


