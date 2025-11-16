import telebot
import requests
import re
import json
import os
from urllib.parse import urlparse, parse_qs

# --- КОНФИГУРАЦИЯ ---
TOKEN = '8455959886:AAGqbIM-BF32QqPhS4u-R-N602oik7nZFxE' 
bot = telebot.TeleBot(TOKEN)
TIKTOK_URL_PATTERN = re.compile(r'^(https?://)?(www\.|vm\.|vt\.)?(tiktok\.com|vt\.tiktok\.com)/[a-zA-Z0-9\-\.\/\?\_=&%]+')

# --- НОВЫЕ КОНСТАНТЫ ДЛЯ АДМИНА И БАЗЫ ДАННЫХ ---
OWNER_ID = 8034775567  # ID владельца
USERS_DB = 'users.json'

# --- ФУНКЦИИ БАЗЫ ДАННЫХ (JSON) ---

def load_users():
    """Загружает список chat_id из файла."""
    if os.path.exists(USERS_DB):
        try:
            with open(USERS_DB, 'r', encoding='utf-8') as f:
                # Преобразуем загруженные строки/числа в set для уникальности
                data = json.load(f)
                return {int(uid) for uid in data} if isinstance(data, list) else set()
        except json.JSONDecodeError:
            # Обработка случая, если файл пуст или поврежден
            return set()
    return set()

def save_users(users):
    """Сохраняет список chat_id в файл."""
    # Конвертируем set в list для JSON-сериализации
    with open(USERS_DB, 'w', encoding='utf-8') as f:
        json.dump(list(users), f, ensure_ascii=False, indent=4)

def add_user(chat_id):
    """Добавляет нового пользователя, если его нет."""
    users = load_users()
    if chat_id not in users:
        users.add(chat_id)
        save_users(users)
        return True
    return False

# --- УТИЛИТЫ и API (Оставлены без изменений) ---

def get_full_url(url):
    """Преобразует короткую ссылку (vt.tiktok.com) в полную."""
    try:
        if 'vt.tiktok.com' in url or 'vm.tiktok.com' in url:
            response = requests.get(url, allow_redirects=True, timeout=10)
            return response.url
        return url
    except Exception:
        return url

def get_tiktok_video_no_watermark(url):
    """
    Получение ссылки на контент без водяного знака с использованием 
    внешнего, стабильного API-сервиса (tikwm.com).
    Возвращает: content_type, content_data (URL/список), audio_url
    """
    full_url = get_full_url(url)
    api_endpoint = "https://www.tikwm.com/api/" 
    
    payload = {
        'url': full_url,
        'hd': 1 
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        response = requests.post(api_endpoint, data=payload, headers=headers, timeout=20)
        response.raise_for_status() 
        data = response.json()
        
        audio_url = None
        
        if data.get('code') == 0 and 'data' in data:
            result = data['data']
            
            if 'music' in result and result['music']:
                audio_url = result['music']
            
            if 'images' in result and result['images']:
                 if result['images']:
                    return "photo", result['images'], audio_url
            
            if 'hdplay' in result and result['hdplay']:
                 return "video", result['hdplay'], audio_url
            elif 'play' in result and result['play']:
                 return "video", result['play'], audio_url
                 
            return "error", "API вернул данные, но не нашел ссылок для скачивания (видео/фото).", None
            
        else:
            return "error", f"Внешний API-сервис отклонил запрос: {data.get('msg', 'Неизвестная ошибка')}", None

    except requests.exceptions.RequestException as e:
        return "error", f"Ошибка при подключении к внешнему API-сервису: {e}", None
    except Exception as e:
        return "error", f"Критическая ошибка при парсинге данных API: {e}", None

# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # Сохраняем пользователя
    add_user(message.chat.id) 
    bot.reply_to(message, 
                 "Привет! Я бот для скачивания контента из TikTok без водяного знака.\n"
                 "Просто отправь мне ссылку на видео или набор фотографий из TikTok.")

@bot.message_handler(func=lambda message: TIKTOK_URL_PATTERN.search(message.text.strip()))
def handle_tiktok_link(message):
    # Сохраняем пользователя
    add_user(message.chat.id) 
    link = message.text.strip()

    try:
        processing_msg = bot.send_message(message.chat.id, 
                                          "🤖 Начинаю обработку ссылки. Пожалуйста, подождите...")
        
        content_type, content_data, audio_url = get_tiktok_video_no_watermark(link)
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # --- ФОРМИРОВАНИЕ КНОПКИ (С прямой ссылкой на аудио) ---
        keyboard = None
        if audio_url:
            keyboard = telebot.types.InlineKeyboardMarkup()
            audio_button = telebot.types.InlineKeyboardButton(text="🎵 Трек", url=audio_url)
            keyboard.add(audio_button)

        # --- ОБРАБОТКА КОНТЕНТА ---
        if content_type == "video" and content_data:
            bot.send_chat_action(message.chat.id, 'upload_video')
            
            video_headers = {'User-Agent': 'Mozilla/5.0'} 
            video_file = requests.get(content_data, headers=video_headers, stream=True, timeout=60)
            
            new_video_caption = "✅  Видео скачано с помощью **@webloliSaveBot**"
            
            bot.send_video(message.chat.id, 
                           video_file.content, 
                           caption=new_video_caption,
                           parse_mode='Markdown', 
                           reply_markup=keyboard,
                           supports_streaming=True)
                           
        elif content_type == "photo" and isinstance(content_data, list) and content_data:
            media = []
            photo_headers = {'User-Agent': 'Mozilla/5.0'} 
            
            new_photo_caption = "✅ Фотографии TikTok скачано с помощью **@webloliSaveBot**"
            
            for i, url in enumerate(content_data):
                if i < 10: 
                    photo_bytes = requests.get(url, headers=photo_headers, timeout=10).content
                    
                    photo_media = telebot.types.InputMediaPhoto(photo_bytes)
                    if i == 0:
                         photo_media.caption = new_photo_caption
                         photo_media.parse_mode = 'Markdown' 
                    media.append(photo_media)

            if media:
                bot.send_media_group(message.chat.id, media)
                
                # Отправка отдельного сообщения с кнопкой для фотопоста
                if keyboard:
                    bot.send_message(message.chat.id, 
                                     "🎵 Аудио-трек:", 
                                     reply_markup=keyboard, 
                                     disable_notification=True)
            else:
                 bot.reply_to(message, "Не удалось найти фотографии в посте.")
            
        elif content_type == "error":
             bot.reply_to(message, f"❌ Ошибка: {content_data}")
             
        else:
            bot.reply_to(message, 
                         "❌ Не удалось получить контент. Возможно, пост приватен или API-метод устарел.")

    except Exception as e:
        print(f"Произошла критическая ошибка при обработке: {e}")
        bot.reply_to(message, 
                     "Критическая ошибка при обработке запроса. Попробуйте другую ссылку.")
        
# --- АДМИН ПАНЕЛЬ (/admin) ---

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    # Проверка ID владельца
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "Доступ запрещен.")
        return

    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        telebot.types.InlineKeyboardButton("📢 Начать рассылку", callback_data="admin_broadcast_start")
    )
    bot.send_message(message.chat.id, "🔐 **Админ-панель**\n\nВыберите действие:", 
                     reply_markup=markup, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data.startswith('admin_'))
def admin_callback_query(call):
    bot.answer_callback_query(call.id)
    if call.from_user.id != OWNER_ID:
        return

    # --- СТАТИСТИКА ---
    if call.data == "admin_stats":
        users = load_users()
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📊 **Статистика**\n\nОбщее количество пользователей: **{len(users)}**",
            parse_mode='Markdown',
            reply_markup=None # Удаляем кнопки после действия
        )
    
    # --- НАЧАЛО РАССЫЛКИ (ШАГ 1: Ввод сообщения) ---
    elif call.data == "admin_broadcast_start":
        msg = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📢 **Начало рассылки**\n\nВведите сообщение, которое хотите отправить всем пользователям. \n\n*Для отмены отправьте /cancel*",
            parse_mode='Markdown',
            reply_markup=None
        )
        # Регистрируем следующий шаг для приема сообщения рассылки
        bot.register_next_step_handler(msg, process_broadcast_message)

def process_broadcast_message(message):
    if message.from_user.id != OWNER_ID: return # Дополнительная проверка безопасности

    if message.text == '/cancel':
        bot.send_message(message.chat.id, "Рассылка отменена.")
        return
    
    # Сохраняем текст сообщения, чтобы передать его в финальный шаг
    broadcast_text = message.text
    
    # --- РАССЫЛКА (ШАГ 2: Ввод количества) ---
    msg = bot.send_message(message.chat.id, 
                           "Введите количество пользователей для рассылки (например, **500**). \n\n*Для отправки всем пользователям введите 0 или пропустите этот шаг (нажмите любое нечисловое значение).*")
    
    # Сохраняем сообщение и текст рассылки для следующего шага
    bot.register_next_step_handler(msg, lambda m: start_broadcast(m, broadcast_text))

def start_broadcast(message, broadcast_text):
    if message.from_user.id != OWNER_ID: return

    try:
        # Пытаемся получить число, если не число, то отправляем всем
        limit = int(message.text.strip())
        if limit < 0: raise ValueError
    except (ValueError, AttributeError):
        limit = 0 # Отправить всем
    
    users = load_users()
    user_list = list(users)
    
    # Применяем ограничение
    if limit > 0 and limit < len(user_list):
        recipients = user_list[:limit]
        bot.send_message(message.chat.id, f"Начинаю рассылку для **{len(recipients)}** пользователей...", parse_mode='Markdown')
    else:
        recipients = user_list
        bot.send_message(message.chat.id, f"Начинаю рассылку для **всех {len(recipients)}** пользователей...", parse_mode='Markdown')
        
    sent_count = 0
    blocked_count = 0
    
    # Процесс рассылки
    for chat_id in recipients:
        try:
            bot.send_message(chat_id, broadcast_text)
            sent_count += 1
        except telebot.apihelper.ApiTelegramException as e:
            # 403 Forbidden: Бот заблокирован пользователем.
            if e.result_json.get('error_code') == 403:
                blocked_count += 1
            else:
                print(f"Ошибка при отправке пользователю {chat_id}: {e}")
        except Exception as e:
            print(f"Критическая ошибка при отправке пользователю {chat_id}: {e}")

    # Финальный отчет
    report = (f"📢 **Рассылка завершена!**\n\n"
              f"✅ Отправлено сообщений: **{sent_count}**\n"
              f"🚫 Пользователей заблокировали: **{blocked_count}**\n"
              f"👤 Всего пользователей в базе: **{len(users)}**")
              
    bot.send_message(message.chat.id, report, parse_mode='Markdown')


# --- ЗАПУСК БОТА ---

@bot.message_handler(func=lambda message: True)
def default_response(message):
    # Обработчик для всех остальных сообщений, если они не являются ссылками TikTok.
    add_user(message.chat.id)
    bot.reply_to(message, "Пожалуйста, отправьте корректную ссылку на TikTok.")


print("[DIX]: Бот запущен и готов принимать сообщения...")
# Создаем пустой файл базы данных, если его нет, чтобы избежать ошибок
if not os.path.exists(USERS_DB):
    save_users(set())
    
try:
    bot.infinity_polling()
except Exception as e:
    print(f"Критическая ошибка в работе бота: {e}")
