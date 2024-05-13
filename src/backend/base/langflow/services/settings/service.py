import os

import yaml
from loguru import logger

from langflow.services.base import Service
from langflow.services.settings.auth import AuthSettings
from langflow.services.settings.base import Settings


class SettingsService(Service):
    name = "settings_service"

    def __init__(self, settings: Settings, auth_settings: AuthSettings):
        super().__init__()
        self.settings: Settings = settings
        self.auth_settings: AuthSettings = auth_settings

    @classmethod
    def load_settings_from_yaml(cls, file_path: str) -> "SettingsService":
        settings = Settings()
        if not settings.CONFIG_DIR:
            raise ValueError("CONFIG_DIR must be set in settings")

        auth_settings = AuthSettings(
            CONFIG_DIR=settings.CONFIG_DIR,
        )
        return cls(settings, auth_settings)
