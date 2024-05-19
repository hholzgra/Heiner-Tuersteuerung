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
echo '##@chromium-browser --chrome-frame --kiosk https://about:blank' >> "$AUTOSTART_FILE"

# Installation zusätzlicher Pakete eventuell nötig
pip install nfcpy tomli
sudo apt install python3-systemd
sudo apt install python3-pil.imagetk

# System Services
SYSTEMD_FOLDER="/etc/systemd/system"
sudo cp "$SCRIPT_DIR"/tuer_gpio_backlight_control.service "$SYSTEMD_FOLDER"
sudo cp "$SCRIPT_DIR"/tuer_nfc_sensor.service "$SYSTEMD_FOLDER"

#SYSTEMD_FOLDER_ALT="/etc/systemd/system/multi-user.target.wants"
#sudo cp "$SCRIPT_DIR"/gpio_backlight_control.service "$SYSTEMD_FOLDER_ALT"
#sudo cp "$SCRIPT_DIR"/tuer_nfc_sensor.service "$SYSTEMD_FOLDER_ALT"

sudo systemctl daemon-reload

sudo systemctl enable tuer_gpio_backlight_control.service
sudo systemctl start tuer_gpio_backlight_control.service

sudo systemctl enable tuer_nfc_sensor.service
sudo systemctl start tuer_nfc_sensor.service


chmod +x "$SCRIPT_DIR"/../tuer_gpio_backlight_control.py


