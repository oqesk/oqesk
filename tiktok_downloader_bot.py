import telebot
import requests
import re
from urllib.parse import urlparse, parse_qs

# --- КОНФИГУРАЦИЯ ---
TOKEN = '8455959886:AAGqbIM-BF32QqPhS4u-R-N602oik7nZFxE' 
bot = telebot.TeleBot(TOKEN)
TIKTOK_URL_PATTERN = re.compile(r'^(https?://)?(www\.|vm\.|vt\.)?(tiktok\.com|vt\.tiktok\.com)/[a-zA-Z0-9\-\.\/\?\_=&%]+')

# --- УТИЛИТЫ и API (Без изменений) ---
# ... (Оставим get_full_url и get_tiktok_video_no_watermark как в предыдущем шаге)
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
            
            # Извлекаем ссылку на аудио (трек), если она есть
            if 'music' in result and result['music']:
                audio_url = result['music']
            
            # --- ПРИОРИТЕТ 1: Обработка Фотопоста ---
            if 'images' in result and result['images']:
                 if result['images']:
                    return "photo", result['images'], audio_url
            
            # --- ПРИОРИТЕТ 2: Обработка Видео ---
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


# --- ОБРАБОТЧИКИ СООБЩЕНИЙ (Обновление логики отправки) ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, 
                 "Привет! Я бот для скачивания контента из TikTok без водяного знака.\n"
                 "Просто отправь мне ссылку на видео или набор фотографий из TikTok.")

@bot.message_handler(func=lambda message: True)
def handle_tiktok_link(message):
    link = message.text.strip()
    
    if not TIKTOK_URL_PATTERN.search(link):
        bot.reply_to(message, "Пожалуйста, отправьте корректную ссылку на TikTok.")
        return

    try:
        processing_msg = bot.send_message(message.chat.id, 
                                          "🤖 Начинаю обработку ссылки. Пожалуйста, подождите...")
        
        # Получаем три значения: тип, контент, аудио
        content_type, content_data, audio_url = get_tiktok_video_no_watermark(link)
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        
        # --- ФОРМИРОВАНИЕ КНОПКИ (С прямой ссылкой на аудио) ---
        keyboard = None
        if audio_url:
            keyboard = telebot.types.InlineKeyboardMarkup()
            # Инлайн-кнопка с прямой ссылкой на аудио
            audio_button = telebot.types.InlineKeyboardButton(text="🎵 Трек", url=audio_url)
            keyboard.add(audio_button)

        # --- ОБРАБОТКА КОНТЕНТА ---
        if content_type == "video" and content_data:
            bot.send_chat_action(message.chat.id, 'upload_video')
            
            video_headers = {'User-Agent': 'Mozilla/5.0'} 
            video_file = requests.get(content_data, headers=video_headers, stream=True, timeout=60)
            
            new_video_caption = "✅  Видео скачано с помощью **@webloliSaveBot**"
            
            # Отправка видео
            bot.send_video(message.chat.id, 
                           video_file.content, 
                           caption=new_video_caption,
                           parse_mode='Markdown', 
                           reply_markup=keyboard, # Добавляем кнопку
                           supports_streaming=True)
                           
            # ОТПРАВКА АУДИО ТРЕКА ОТДЕЛЬНЫМ СООБЩЕНИЕМ
            if audio_url:
                try:
                    bot.send_chat_action(message.chat.id, 'upload_audio')
                    # Отправляем аудио по URL, имитируя голосовое сообщение
                    audio_headers = {'User-Agent': 'Mozilla/5.0'}
                    audio_file = requests.get(audio_url, headers=audio_headers, stream=True, timeout=30).content
                    
                    # Отправляем как аудиофайл
                    bot.send_audio(message.chat.id, 
                                   audio_file, 
                                   caption="🎵 Оригинальный трек", 
                                   title="Трек с TikTok")
                except Exception as audio_e:
                    print(f"Не удалось отправить аудиофайл: {audio_e}")


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
                # Отправка медиагруппы
                bot.send_media_group(message.chat.id, media)
                
                # ОТПРАВКА АУДИО ТРЕКА ОТДЕЛЬНЫМ СООБЩЕНИЕМ ДЛЯ ФОТОПОСТА
                if audio_url:
                    try:
                        bot.send_chat_action(message.chat.id, 'upload_audio')
                        audio_headers = {'User-Agent': 'Mozilla/5.0'}
                        audio_file = requests.get(audio_url, headers=audio_headers, stream=True, timeout=30).content
                        
                        bot.send_audio(message.chat.id, 
                                       audio_file, 
                                       caption="🎵 Оригинальный трек", 
                                       title="Трек с TikTok")
                    except Exception as audio_e:
                        print(f"Не удалось отправить аудиофайл: {audio_e}")
                        
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

# --- ЗАПУСК БОТА ---

print("[DIX]: Бот запущен и готов принимать сообщения...")
try:
    bot.infinity_polling()
except Exception as e:
    print(f"Критическая ошибка в работе бота: {e}")
