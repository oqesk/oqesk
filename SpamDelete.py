# Модуль для накрутки сообщений с удалением
# meta developer: @oqesk

from .. import loader, utils
from hikkatl.types import Message
import asyncio

@loader.tds
class SpamDeleteMod(loader.Module):
    """Спам сообщениями с автоматическим удалением"""
    strings = {
        "name": "EblaSpam",
        "args": "✖️ Используйте: <code>.ebla [текст] [количество]</code>",
        "num_error": "✖️ Укажите корректное число повторений (1-1000)",
        "limit_error": "✖️ Максимум 1000 повторений",
        "start": "🔄 Начинаю спам...",
        "done": "✅ Готово! Сообщения отправлены и удалены",
        "stopped": "⏹️ Спам остановлен!",
        "not_running": "ℹ️ Нет активного спама для остановки"
    }

    def __init__(self):
        self.is_spamming = False
        self.current_task = None

    async def client_ready(self, client, db):
        self._client = client

    @loader.command(ru_doc="[текст] [кол-во] - Спам с удалением")
    async def eblacmd(self, message: Message):
        """Спам сообщениями с автоподчисткой"""
        if self.is_spamming:
            await utils.answer(message, "✖️ Спам уже запущен! Используйте <code>.eblaoff</code> для остановки")
            return

        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        try:
            parts = args.rsplit(" ", 1)
            if len(parts) < 2:
                raise ValueError
            text, count = parts
            count = int(count)
        except ValueError:
            await utils.answer(message, self.strings("args"))
            return

        if count <= 0:
            await utils.answer(message, self.strings("num_error"))
            return
        
        if count > 1000:
            await utils.answer(message, self.strings("limit_error"))
            return

        await utils.answer(message, self.strings("start"))
        await message.delete()

        self.is_spamming = True
        self.current_task = asyncio.create_task(self._spam_task(message, text, count))

    async def _spam_task(self, message, text, count):
        try:
            for i in range(count):
                if not self.is_spamming:
                    break
                    
                msg = await self._client.send_message(
                    message.peer_id,
                    text,
                    silent=True
                )
                await asyncio.sleep(0.3)
                await msg.delete()
                await asyncio.sleep(0.3)
        finally:
            self.is_spamming = False
            if self.is_spamming:  # Если остановлено вручную
                notify = await message.respond(self.strings("stopped"))
            else:  # Если завершено полностью
                notify = await message.respond(self.strings("done"))
            await asyncio.sleep(3)
            await notify.delete()

    @loader.command(ru_doc="Остановить текущий спам")
    async def eblaoffcmd(self, message: Message):
        """Остановить текущий спам"""
        if not self.is_spamming:
            await utils.answer(message, self.strings("not_running"))
            return
            
        self.is_spamming = False
        if self.current_task:
            self.current_task.cancel()
        await utils.answer(message, self.strings("stopped"))
        # Модуль для накрутки сообщений с удалением
# meta developer: @oqesk

from .. import loader, utils
from hikkatl.types import Message
import asyncio

@loader.tds
class SpamDeleteMod(loader.Module):
    """Спам сообщениями с автоматическим удалением"""
    strings = {
        "name": "EblaSpam",
        "args": "✖️ Используйте: <code>.ebla [текст] [количество]</code>",
        "num_error": "✖️ Укажите корректное число повторений (1-1000)",
        "limit_error": "✖️ Максимум 1000 повторений",
        "start": "🔄 Начинаю спам...",
        "done": "✅ Готово! Сообщения отправлены и удалены",
        "stopped": "⏹️ Спам остановлен!",
        "not_running": "ℹ️ Нет активного спама для остановки"
    }

    def __init__(self):
        self.is_spamming = False
        self.current_task = None

    async def client_ready(self, client, db):
        self._client = client

    @loader.command(ru_doc="[текст] [кол-во] - Спам с удалением")
    async def eblacmd(self, message: Message):
        """Спам сообщениями с автоподчисткой"""
        if self.is_spamming:
            await utils.answer(message, "✖️ Спам уже запущен! Используйте <code>.eblaoff</code> для остановки")
            return

        args = utils.get_args_raw(message)
        
        if not args:
            await utils.answer(message, self.strings("args"))
            return

        try:
            parts = args.rsplit(" ", 1)
            if len(parts) < 2:
                raise ValueError
            text, count = parts
            count = int(count)
        except ValueError:
            await utils.answer(message, self.strings("args"))
            return

        if count <= 0:
            await utils.answer(message, self.strings("num_error"))
            return
        
        if count > 1000:
            await utils.answer(message, self.strings("limit_error"))
            return

        await utils.answer(message, self.strings("start"))
        await message.delete()

        self.is_spamming = True
        self.current_task = asyncio.create_task(self._spam_task(message, text, count))

    async def _spam_task(self, message, text, count):
        try:
            for i in range(count):
                if not self.is_spamming:
                    break
                    
                msg = await self._client.send_message(
                    message.peer_id,
                    text,
                    silent=True
                )
                await asyncio.sleep(0.3)
                await msg.delete()
                await asyncio.sleep(0.3)
        finally:
            self.is_spamming = False
            if self.is_spamming:  # Если остановлено вручную
                notify = await message.respond(self.strings("stopped"))
            else:  # Если завершено полностью
                notify = await message.respond(self.strings("done"))
            await asyncio.sleep(3)
            await notify.delete()

    @loader.command(ru_doc="Остановить текущий спам")
    async def eblaoffcmd(self, message: Message):
        """Остановить текущий спам"""
        if not self.is_spamming:
            await utils.answer(message, self.strings("not_running"))
            return
            
        self.is_spamming = False
        if self.current_task:
            self.current_task.cancel()
        await utils.answer(message, self.strings("stopped"))
        await asyncio.sleep(3)
        await message.delete()await asyncio.sleep(3)
        await message.delete()
