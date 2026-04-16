import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import time
import json
import os
from datetime import datetime, timedelta
import logging

# ========== НАСТРОЙКИ ==========
GROUP_TOKEN = "vk1.a.806l_tSfUkkCH-1LZ_I5i2WNXJHMycnW0VuT01easRPe6KO4SYOHjRapm45KQ1oAeAkg846sGfFOgrDaAVl5yui5QPXDBw5z2Hdp3GBOfT5VGVo4PN2kqzffhdNwgk-5vAguyw5ttL7G6WTU0qbNEmL3VRo3Oizxxy-HuyTD0JNmmxnNKnfStVGKBotpxGtKTC4ayB-84NLocyLSbF99FQ"
WEATHER_API_KEY = "8deab182c13fc938c196ae3931336f9a"
DEFAULT_CITY = "Moscow"

CITIES_FILE = "user_cities.json"
# ================================

# Настройка логов (чтобы видеть что происходит на сервере)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_user_cities():
    if os.path.exists(CITIES_FILE):
        try:
            with open(CITIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_cities(user_cities):
    try:
        with open(CITIES_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_cities, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

def get_user_city(user_id, user_cities):
    return user_cities.get(str(user_id), DEFAULT_CITY)

def set_user_city(user_id, city, user_cities):
    user_cities[str(user_id)] = city
    save_user_cities(user_cities)

def get_current_weather(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if response.status_code == 200:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description']
            humidity = data['main']['humidity']
            wind = data['wind']['speed']
            city_name = data['name']
            message = f"🌤 *Погода в {city_name} сейчас:*\n🌡 {temp}°C (ощущается {feels_like}°C)\n📝 {description.capitalize()}\n💧 Влажность: {humidity}%\n💨 Ветер: {wind} м/с"
            if 'дождь' in description.lower():
                message += "\n☔️ *Не забудьте зонт!*"
            return message, True
        else:
            return f"❌ Город '{city}' не найден.", False
    except Exception as e:
        return f"❌ Ошибка: {e}", False

def get_forecast_for_datetime(city, api_key, target_datetime):
    geo_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    try:
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()
        if geo_response.status_code != 200:
            return f"❌ Город '{city}' не найден.", False
        lat = geo_data['coord']['lat']
        lon = geo_data['coord']['lon']
        forecast_url = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=ru"
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_data = forecast_response.json()
        if forecast_response.status_code != 200:
            return "❌ Не удалось получить прогноз.", False
        closest_forecast = None
        min_time_diff = timedelta(hours=6)
        for item in forecast_data['list']:
            forecast_time = datetime.fromtimestamp(item['dt'])
            time_diff = abs(forecast_time - target_datetime)
            if time_diff < min_time_diff:
                min_time_diff = time_diff
                closest_forecast = item
        if closest_forecast is None:
            return f"❌ Не найден прогноз для {target_datetime.strftime('%d.%m.%Y %H:%M')}", False
        forecast_time = datetime.fromtimestamp(closest_forecast['dt'])
        temp = closest_forecast['main']['temp']
        feels_like = closest_forecast['main']['feels_like']
        description = closest_forecast['weather'][0]['description']
        message = f"📅 *Прогноз в {city}*\n🗓 {forecast_time.strftime('%d.%m.%Y %H:%M')}\n🌡 {temp}°C (ощущается {feels_like}°C)\n📝 {description.capitalize()}"
        return message, True
    except Exception as e:
        return f"❌ Ошибка: {e}", False

def parse_date_time(text):
    now = datetime.now()
    text_lower = text.lower()
    if 'завтра' in text_lower:
        target_date = now + timedelta(days=1)
    elif 'послезавтра' in text_lower:
        target_date = now + timedelta(days=2)
    else:
        target_date = now
    hour = 9
    minute = 0
    import re
    time_patterns = [
        (r'(\d+)\s*:\s*(\d+)', lambda h, m: (int(h), int(m))),
        (r'(\d+)\s*утра', lambda h, m: (int(h), 0)),
        (r'(\d+)\s*вечера', lambda h, m: (int(h) + 12 if int(h) < 12 else int(h), 0)),
    ]
    for pattern, handler in time_patterns:
        match = re.search(pattern, text_lower)
        if match:
            groups = match.groups()
            if len(groups) == 1:
                hour = handler(groups[0], None)[0]
            else:
                hour, minute = handler(groups[0], groups[1])
            break
    target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_datetime < now:
        target_datetime += timedelta(days=1)
    return target_datetime

def send_message(vk, user_id, message):
    try:
        vk.messages.send(user_id=user_id, message=message, random_id=0)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return False

def start_bot():
    while True:
        try:
            user_cities = load_user_cities()
            logger.info(f"Загружено {len(user_cities)} сохраненных городов")
            vk_session = vk_api.VkApi(token=GROUP_TOKEN)
            vk = vk_session.get_api()
            longpoll = VkLongPoll(vk_session)
            logger.info("✅ Бот погоды запущен!")
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    user_id = event.user_id
                    message_text = event.text.lower().strip()
                    logger.info(f"Получено от {user_id}: {message_text}")
                    current_city = get_user_city(user_id, user_cities)
                    if message_text.startswith('город '):
                        new_city = message_text.replace('город ', '').strip()
                        weather, success = get_current_weather(new_city, WEATHER_API_KEY)
                        if success:
                            set_user_city(user_id, new_city, user_cities)
                            send_message(vk, user_id, f"✅ Город изменен на {new_city.capitalize()}!")
                        else:
                            send_message(vk, user_id, f"❌ Город '{new_city}' не найден.")
                    elif message_text == 'мой город':
                        send_message(vk, user_id, f"🏙 Ваш город: {current_city.capitalize()}")
                    elif message_text.startswith('прогноз'):
                        datetime_text = message_text.replace('прогноз', '').replace('на', '').strip()
                        target_datetime = parse_date_time(datetime_text)
                        forecast, success = get_forecast_for_datetime(current_city, WEATHER_API_KEY, target_datetime)
                        send_message(vk, user_id, forecast)
                    elif message_text in ['погода', 'погода?', 'какая погода']:
                        weather, success = get_current_weather(current_city, WEATHER_API_KEY)
                        send_message(vk, user_id, weather)
                    elif message_text in ['привет', 'ку', 'start']:
                        send_message(vk, user_id, f"Привет! Я бот погоды.\nСейчас в {current_city} напиши 'погода'\nСменить город: 'город Лондон'\nПрогноз: 'прогноз на 9 утра 10 апреля'")
                    elif message_text in ['помощь', 'help']:
                        help_text = "Команды:\nпогода - сейчас\nпрогноз на 9 утра 10 апреля - на дату\nгород Москва - сменить город\nмой город - текущий город"
                        send_message(vk, user_id, help_text)
                    else:
                        send_message(vk, user_id, f"Напишите 'помощь' для списка команд")
        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            logger.info("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()
