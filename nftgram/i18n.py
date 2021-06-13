from contextvars import ContextVar
from pathlib import Path

from aiogram.contrib.middlewares.i18n import I18nMiddleware


class I18nMiddlewareProxy(I18nMiddleware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ctx_locale = ContextVar(self.ctx_locale.name, default=self.default)

    async def get_user_locale(self, *args, **kwargs) -> str:
        # Fixes https://github.com/aiogram/aiogram/issues/562
        language = await super().get_user_locale(*args, **kwargs)
        return language if language and language in self.locales else self.default


_ = i18n = I18nMiddlewareProxy("bot", Path(__file__).parents[1] / "locales", "ru")
