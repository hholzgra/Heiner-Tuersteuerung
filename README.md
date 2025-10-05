# Tür- und Klingelsteuerung

Upstream Repository: https://github.com/medienelektronik/Tuersteuerung


Die Türsteuerung nutzt einen RaspberryPi mit Touchscreen und zusätzlicher
Hardware als integierte Klingelanlage.

Das Touch-Display kann drei beschriftete Klingelknöpfe anzeigen oder über
eine Zahlencode-Eingabe auch direkt zur Türöffnung genutzt werden.

Über vier Relais können zwei Klingeln, Türöffner und Briefkastenöffner
angesteuert werden.

Ein NFC-Reader ermöglicht das Öffnen der Tür mit Schlüsselkarten oder
-tokens, und ein Radar-Näherungssensor aktiviert das Display sobald 
sich eine Person vor der Klingelanlage befindet.


## Hardware

* Raspberry Pi
* Raspberry 7" Touch Display
* 4fach I2C Relais-Karte
* NFC/RFID Reader
* Radar-Näherungssensor
* Lautsprecher


## Installation

Zur Zeit dient dazu das Script `FirstRunInstall/InstallRunOnce.sh`


### Python-Pakete

Eine Liste der nötigen PIP Pakete finded sich in der Datei `requrements.txt`

### SystemD Services

...


## Konfiguration

Die verschiedenen Komponenten werden weitgehend über die `einstellungen.txt`
konfiguriert. Diese hat zur Zeit vier Abschnitte `[tuer]`, `[namen]`, `[nfc]` 
und `telegram`.

### `[tuer]`

* `zugangscode`: Zahlenkombination zum Öffnen der Tür
* `herunterfahren`: Zugangscode zum Abschalten der Türsteuerung

### `[namen]`

* `oben`: Beschriftung für das obere Klingelschild
* `mitte`: Beschriftung für das mittlere Klingelschild
* `unten`: Beschriftung für das untere Klingelschild

### `[nfc]`

* `tokens`: Liste der Seriennummern gültiger Schlüsseltoken zum Öffnen der Tür

### `[telegram]`

* `CHAT_ID`: Name eines Telegram Chats für Benachrichtigungen
* `TOKEN`: Telegram-Zugriffstoken


## ... misc ...


## Fehlersuche
Falls im syslog nichts steht dann steht vielleicht hier was:
/home/pi/.cache/lxsession/LXDE-pi/run.log


