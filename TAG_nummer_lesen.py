import nfc
import binascii

# Erstelle ein "Contactless Frontend" (clf)
clf = nfc.ContactlessFrontend()
# Öffne das NFC Modul an der seriellen Schnittstelle
assert clf.open('tty:S0:pn532') is True
# Stelle Verbindung zu einem NFC Tag her
tag = clf.connect(rdwr={'on-connect': lambda tag: False})

if tag.is_present is True:
    print("Tag gefunden")

#Zeige Seriennummer an
seriennummer=binascii.hexlify(tag.identifier).decode('UTF-8')
print(seriennummer)

if seriennummer == "bc75ed67":
    print("Richtige Karte!")
    # Hier Tuer oeffnen
else:
    print("Falsche Karte!")

# Schließe clf
clf.close()