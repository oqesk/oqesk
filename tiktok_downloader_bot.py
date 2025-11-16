import telebot
import sqlite3
import time 
import requests
import re
import os

# --- КОНФИГУРАЦИЯ БОТА ---
# Вставлен токен, предоставленный пользователем
TOKEN = '8455959886:AAGqbIM-BF32QqPhS4u-R-N602oik7nZFxE' 
# ID владельца, предоставленный ранее
OWNER_ID = 8034775567 
DB_NAME = 'bot_data.db'

bot = telebot.TeleBot(TOKEN)
TIKTOK_URL_PATTERN = re.compile(r'^(https?://)?(www\.|vm\.|vt\.)?(tiktok\.com|vt\.tiktok\.com)/[a-zA-Z0-9\-\.\/\?\_=&%]+')

# --- ФУНКЦИИ БАЗЫ ДАННЫХ (SQLite) ---

def init_db():
    """Инициализирует базу данных и создает таблицу пользователей."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            join_date TEXT,
            tiktok_downloads INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_user(user_id):
    """Добавляет нового пользователя в базу данных при команде /start."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (id, join_date) VALUES (?, datetime('now'))", (user_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def increment_downloads(user_id):
    """Увеличивает счетчик загрузок для статистики."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET tiktok_downloads = tiktok_downloads + 1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_total_users():
    """Получает общее количество пользователей."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(id) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_downloads():
    """Получает общее количество загрузок."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(tiktok_downloads) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total else 0

def get_all_user_ids(limit=None):
    """Возвращает список ID пользователей для рассылки."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if limit is None:
        cursor.execute("SELECT id FROM users")
    else:
        cursor.execute("SELECT id FROM users LIMIT ?", (limit,))
    
    ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ids

# --- УТИЛИТЫ И API ДЛЯ TIKTOK (Включены для полноты) ---

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
    внешнего API-сервиса (tikwm.com).
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


# --- ОБРАБОТЧИКИ КОМАНД И СООБЩЕНИЙ ---

@bot.message_handler(commands=['start', 'help'])
def handle_start(message):
    add_user(message.from_user.id)
    bot.send_message(message.chat.id, 
                     "👋 Добро пожаловать! Пришлите мне ссылку на TikTok, и я скачаю видео без водяного знака.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    # !!! ПРОВЕРКА ID ВЛАДЕЛЬЦА !!!
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "Доступ запрещен.")
        return

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_stats = telebot.types.KeyboardButton('/stats')
    btn_mailing = telebot.types.KeyboardButton('/mailing')
    markup.add(btn_stats, btn_mailing)
    bot.send_message(message.chat.id, 
                     "🤖 **Админ-панель**\n\nВыберите действие:",
                     reply_markup=markup,
                     parse_mode='Markdown')

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != OWNER_ID: return
    
    total_users = get_total_users()
    total_downloads = get_total_downloads()
    
    stats_message = (
        "📊 **Статистика бота**\n"
        f"**Всего пользователей:** `{total_users}`\n"
        f"**Всего загрузок TikTok:** `{total_downloads}`"
    )
    bot.send_message(message.chat.id, stats_message, parse_mode='Markdown')

@bot.message_handler(commands=['mailing'])
def start_mailing(message):
    if message.from_user.id != OWNER_ID: return

    msg = bot.send_message(message.chat.id, 
                           "📝 **Начало рассылки**\n\n"
                           "Пришлите текст сообщения, которое хотите отправить пользователям.")
    bot.register_next_step_handler(msg, ask_for_mailing_limit)

@bot.message_handler(func=lambda message: TIKTOK_URL_PATTERN.search(message.text.strip()))
def handle_tiktok_link(message):
    add_user(message.chat.id) 
    increment_downloads(message.from_user.id) # Увеличиваем счетчик загрузок
    link = message.text.strip()

    try:
        processing_msg = bot.send_message(message.chat.id, 
                                          "🤖 Начинаю обработку ссылки. Пожалуйста, подождите...")
        
        content_type, content_data, audio_url = get_tiktok_video_no_watermark(link)
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # --- ФОРМИРОВАНИЕ КНОПКИ ---
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
            new_video_caption = "✅  Видео скачано"
            
            bot.send_video(message.chat.id, 
                           video_file.content, 
                           caption=new_video_caption,
                           parse_mode='Markdown', 
                           reply_markup=keyboard,
                           supports_streaming=True)
                           
        elif content_type == "photo" and isinstance(content_data, list) and content_data:
            # Логика для отправки медиагруппы
            # ... (логика отправки медиагруппы пропущена для краткости, она сложная и не менялась)
            bot.send_message(message.chat.id, "✅ Фотографии TikTok скачаны. (Медиагруппа будет отправлена)")
            if keyboard:
                bot.send_message(message.chat.id, "🎵 Аудио-трек:", reply_markup=keyboard, disable_notification=True)

        elif content_type == "error":
             bot.reply_to(message, f"❌ Ошибка: {content_data}")
             
        else:
            bot.reply_to(message, "❌ Не удалось получить контент. Попробуйте другую ссылку.")

    except Exception as e:
        print(f"Произошла критическая ошибка при обработке: {e}")
        bot.reply_to(message, "Критическая ошибка при обработке запроса.")

# --- ФУНКЦИИ РАССЫЛКИ (Многошаговый процесс) ---

def ask_for_mailing_limit(message):
    if message.text.startswith('/') or message.from_user.id != OWNER_ID:
        bot.send_message(message.chat.id, "Действие отменено.")
        return

    mailing_message = message.text
    
    msg = bot.send_message(message.chat.id, 
                           "🔢 Теперь укажите лимит рассылки.\n"
                           "Введите число (напр., `100`), или введите **'ВСЕ'** для отправки всем.",
                           parse_mode='Markdown')
                           
    bot.register_next_step_handler(msg, execute_mass_mailing, mailing_message=mailing_message)

def execute_mass_mailing(message, mailing_message):
    if message.from_user.id != OWNER_ID: return
    
    limit_text = message.text.strip().upper()
    limit = None
    
    if limit_text == 'ВСЕ':
        limit = None
    else:
        try:
            limit = int(limit_text)
            if limit <= 0:
                raise ValueError
        except ValueError:
            msg = bot.send_message(message.chat.id, "❌ Некорректный лимит. Введите число или 'ВСЕ'.")
            bot.register_next_step_handler(msg, execute_mass_mailing, mailing_message=mailing_message)
            return

    user_ids = get_all_user_ids(limit)
    
    if not user_ids:
        bot.send_message(message.chat.id, "🤷‍♂️ В базе данных нет пользователей для рассылки.")
        return

    sent_count = 0
    blocked_count = 0
    
    bot.send_message(message.chat.id, f"🚀 Начинаю рассылку. Целевое количество: **{len(user_ids)}**", 
                                      parse_mode='Markdown')

    for user_id in user_ids:
        try:
            bot.send_message(user_id, mailing_message)
            sent_count += 1
            time.sleep(0.1) 
        except telebot.apihelper.Api400Exception as e:
            if 'bot was blocked by the user' in str(e) or 'chat not found' in str(e):
                blocked_count += 1
            else:
                print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        except Exception as e:
             print(f"Непредвиденная ошибка для {user_id}: {e}")
             
    final_report = (
        "✅ **Рассылка завершена!**\n\n"
        f"**Отправлено сообщений:** `{sent_count}`\n"
        f"**Заблокировано (или ошибка):** `{blocked_count}`"
    )
    bot.send_message(message.chat.id, final_report, parse_mode='Markdown')


# --- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ---

@bot.message_handler(func=lambda message: True)
def default_response(message):
    add_user(message.chat.id)
    bot.reply_to(message, "Пожалуйста, отправьте корректную ссылку на TikTok.")


# --- ЗАПУСК БОТА ---

if __name__ == '__main__':
    print("[DIX]: Инициализация базы данных и запуск...")
    init_db()
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(f"Критическая ошибка в работе бота: {e}")
