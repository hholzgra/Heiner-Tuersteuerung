Project download:
in homeverzeichnis wechseln `/home/raspberry/`
git clone git@wilson.ipv64.net:knackwurst/heinerv5.git system_services_tuer



sreensaver optionen in .bashrc gesetzt


systemd service script 
zu finden unter:
 /etc/systemd/system/gpio_backlight_control.service


------------------------------
[Unit]
Description=Horcht auf dem GPIO 19 und schaltet dann den screensaver ab
After=multi-user.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/python /home/raspberry/system_services_tuer/tuer_gpio_backlight_control.py
User=raspberry

[Install]
WantedBy=multi-user.target



/etc/systemd/system/tuer_nfc_sensor.service :
-----------------------------------------

[Unit]
Description=Horcht am NFC Sensor und schaltet die das Relais
After=multi-user.target

[Service]
Type=simple
Restart=always
ExecStart=/usr/bin/python /home/raspberry/system_services_tuer/tuer_gpio_backlight_control.py
User=raspberry

[Install]
WantedBy=multi-user.target



------------------------------------------------------
Fuer blanken Bildschirm und kiosk modus chrome
/home/raspberry/.config/lxsession/LXDE-pi/autostart


xset s 0 0
@xset s noblank
@xset s noexpose
@xset dpms 0 0 20
@python /home/raspberry/system_services_tuer/tuer_klingel_GUI_mitRelais.py




-----------------------------------

Pi Clone von Terminal:

sudo dbus-launch piclone


-----------------------------------

Installation zusätzlicher Pakete eventuell nötig:


pip install nfcpy tomli
sudo apt install python3-systemd
sudo apt install python3-pil.imagetk