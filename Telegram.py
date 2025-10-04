import requests

from Settings import Settings

def bot_notification(message: str, demo_modus = False):
        """Sendet eine Nachricht an den mit TOKEN und CHAT_ID konfigurierten Telegram Bot"""

        settings = Settings()
        setup    = settings.get("telegram")
        
        url = f"https://api.telegram.org/bot{setup['TOKEN']}/sendMessage?chat_id={setup['CHAT_ID']}&text={message}"

        if demo_modus:
            print(f"DEMO::TelegramMsg:  {url}")
            return

        try:
            requests.get(url)
            print("GESENDET")
        except:
            print("SENDE FEHLER")
            pass
