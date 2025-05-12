from hikkatl.types import Message
from hikka import loader, utils
import logging

logger = logging.getLogger(__name__)

@loader.tds
class AutoQuoteOqeskMod(loader.Module):
    """Автоматическое цитирование сообщений от @oqesk"""
    
    strings = {
        "name": "AutoQuoteOqesk",
        "on": "✅ <b>Автоцитирование @oqesk включено</b>",
        "off": "❌ <b>Автоцитирование @oqesk выключено</b>"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ENABLED",
            False,
            "Статус модуля"
        )

    async def client_ready(self, client, db):
        self._client = client

    @loader.watcher(out=True)
    async def watcher(self, message: Message):
        if not self.config["ENABLED"]:
            return
            
        # Проверяем, что сообщение отправлено @oqesk
        sender = await message.get_sender()
        if not sender or getattr(sender, "username", "").lower() != "oqesk":
            return
            
        # Проверяем, что сообщение не команда и еще не цитируется
        if message.raw_text and not message.raw_text.startswith(("<blockquote>", "!")):
            try:
                await message.edit(f"<blockquote>{message.raw_text}</blockquote>")
            except Exception as e:
                logger.error(f"Failed to edit message: {e}")

    @loader.command()
    async def aoqcmd(self, message: Message):
        """Переключить автоцитирование @oqesk"""
        self.config["ENABLED"] = not self.config["ENABLED"]
        status = self.strings["on"] if self.config["ENABLED"] else self.strings["off"]
        await utils.answer(message, status)
