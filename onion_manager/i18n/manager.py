"""Language manager: loads lang.json and provides translation helper."""
import json
import os
from typing import Dict
from onion_manager import config


class LanguageManager:
    def __init__(self, lang_file: str = None):
        self.lang_file = lang_file or config.LANG_FILE
        self.strings: Dict[str, Dict[str, str]] = {}
        self.current_lang = 'ru'
        self._load_languages()

    def _load_languages(self):
        try:
            with open(self.lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.strings = data
        except Exception:
            # fallback
            self.strings = {
                'ru': {'window_title': 'Onion Manager'},
                'en': {'window_title': 'Onion Manager'}
            }

    def tr(self, key: str) -> str:
        return self.strings.get(self.current_lang, {}).get(key, self.strings.get('en', {}).get(key, key))

    def set_language(self, lang: str) -> bool:
        if lang in self.strings:
            self.current_lang = lang
            return True
        return False


# single shared instance
lang_mgr = LanguageManager()
