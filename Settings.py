import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

class Settings:
    _settings = None

    def __init__(self):
        if Settings._settings == None:
            with open(Path("einstellungen.txt"), "rb") as settings_file:
                Settings._settings = tomllib.load(settings_file)
                
    def get(self, name, default = None):
        try:
            return Settings._settings[name]
        except:
            return default

if __name__ == '__main__':
    s1 = Settings()
    s2 = Settings()

    print(s1.get("namen"))
    print(s2.get("namen"))
    print(s1.get("foobar"))
