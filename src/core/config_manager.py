import json
import os
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent.parent / "config.json"

DEFAULT_CONFIG = {
    "output_directory": str(Path.home() / "Desktop" / "DocToMD_Result"),
    "ai_provider": "ollama",
    "ai_model": "gemma4:latest",
    "ollama_base_url": "http://localhost:11434",
    "gemini_api_key": ""
}

class ConfigManager:
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config.update(json.load(f))
            except Exception:
                pass

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
