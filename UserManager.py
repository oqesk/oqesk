import asyncio
from telethon import errors, functions, types
from .. import loader, utils

class UserManagerMod(loader.Module):
    """Модуль для массового переноса и кика пользователей (by @oqesk)"""
    strings = {"name": "UserManager (@oqesk)"}

    async def перенестиcmd(self, event):
        """Добавить всех из текущего чата в целевой (ID или ссылка)"""
        args = utils.get_args_raw(event)
        if not args:
            return await event.edit("❌ <b>Укажите ID чата или ссылку!</b>")

        try:
            target_chat = await event.client.get_entity(args)
        except Exception as e:
            return await event.edit(f"❌ <b>Ошибка: {e}</b>")

        if not isinstance(target_chat, (types.Channel, types.Chat)):
            return await event.edit("❌ <b>Указана не чат/канал!</b>")

        await event.edit("🔍 <b>Собираю пользователей...</b>")
        users = []
        async for user in event.client.iter_participants(event.chat_id):
            if not user.bot and not user.is_self:
                users.append(user)

        if not users:
            return await event.edit("❌ <b>Нет пользователей для переноса!</b>")

        await event.edit(f"🔄 <b>Переношу {len(users)} пользователей...</b>")
        success = 0
        failed = 0

        for user in users:
            try:
                await event.client(
                    functions.channels.InviteToChannelRequest(
                        channel=target_chat,
                        users=[user]
                    )
                )
                success += 1
                await asyncio.sleep(1)  # Защита от флуда
            except errors.UserPrivacyRestrictedError:
                failed += 1  # Пользователь запретил приглашения
            except errors.UserAlreadyParticipantError:
                failed += 1  # Уже в чате
            except errors.FloodWaitError as e:
                await event.edit(f"⏳ <b>Флуд-контроль! Ждем {e.seconds} сек.</b>")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                failed += 1
                await event.reply(f"⚠️ Ошибка с {user.id}: {str(e)}")

        await event.edit(
            f"✅ <b>Готово!</b>\n"
            f"• Успешно: <code>{success}</code>\n"
            f"• Не удалось: <code>{failed}</code>"
        )

    async def kickallcmd(self, event):
        """Кикнуть всех из текущего чата (кроме админов)"""
        if not event.is_channel and not event.is_group:
            return await event.edit("❌ <b>Только для чатов/каналов!</b>")

        await event.edit("🔍 <b>Собираю пользователей...</b>")
        users = []
        async for user in event.client.iter_participants(event.chat_id):
            if not user.is_self:  # Не кикаем себя
                users.append(user)

        if not users:
            return await event.edit("❌ <b>Нет пользователей для кика!</b>")

        await event.edit(f"🔄 <b>Кикаю {len(users)} пользователей...</b>")
        success = 0
        failed = 0

        for user in users:
            try:
                await event.client.kick_participant(event.chat_id, user)
                success += 1
                await asyncio.sleep(1)  # Защита от флуда
            except errors.ChatAdminRequiredError:
                failed += 1  # Нет прав
            except errors.UserNotParticipantError:
                failed += 1  # Уже вышел
            except errors.FloodWaitError as e:
                await event.edit(f"⏳ <b>Флуд-контроль! Ждем {e.seconds} сек.</b>")
                await asyncio.sleep(e.seconds)
            except Exception as e:
                failed += 1
                await event.reply(f"⚠️ Ошибка с {user.id}: {str(e)}")

        await event.edit(
            f"✅ <b>Готово!</b>\n"
            f"• Кикнуто: <code>{success}</code>\n"
            f"• Не удалось: <code>{failed}</code>"
        )