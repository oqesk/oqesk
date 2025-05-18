#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Автор: @oqesk
# Описание: Автоматически преобразует отправленные сообщения в моноширинный формат (как цитату).

from pyrogram import Client, filters
from pyrogram.types import Message

# Конфигурация (замените на свои данные!)
API_ID = 12345  # Получить на my.telegram.org
API_HASH = "abcdef123"
DEV = "@oqesk"  # Разработчик

app = Client("mono_quote_bot", api_id=API_ID, api_hash=API_HASH)

async def send_mono_message(client: Client, message: Message):
    """Удаляет исходное сообщение и отправляет его в моноширинном формате."""
    if not message.text or message.text.startswith('/'):
        return
    
    mono_text = f"`{message.text}`"  # Обёртка в ` ` для monospace
    await message.delete()  # Удаляем исходное сообщение
    
    await client.send_message(
        chat_id=message.chat.id,
        text=f"{mono_text}\n\n`🔹 Разработчик: {DEV}`",  # Добавляем подпись
        reply_to_message_id=message.reply_to_message_id
    )

@app.on_message(filters.text & filters.outgoing)
async def mono_converter(client: Client, message: Message):
    await send_mono_message(client, message)

if __name__ == "__main__":
    print(f"""
╔════════════════════════════╗
║  Модуль моноширинного чата ║
║                            ║
║  Разработчик: {DEV.ljust(15)}║
╚════════════════════════════╝
""")
    app.run()
