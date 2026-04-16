import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import time
import json
import os
from datetime import datetime, timedelta

# ============================================
# 👇👇👇 ВСТАВЬТЕ ВАШИ КЛЮЧИ СЮДА 👇👇👇
# ============================================

VK_TOKEN = "vk1.a.806l_tSfUkkCH-1LZ_I5i2WNXJHMycnW0VuT01easRPe6KO4SYOHjRapm45KQ1oAeAkg846sGfFOgrDaAVl5yui5QPXDBw5z2Hdp3GBOfT5VGVo4PN2kqzffhdNwgk-5vAguyw5ttL7G6WTU0qbNEmL3VRo3Oizxxy-HuyTD0JNmmxnNKnfStVGKBotpxGtKTC4ayB-84NLocyLSbF99FQ"  # ТОКЕН ВКОНТАКТЕ
WEATHER_API_KEY = "8deab182c13fc938c196ae3931336f9a"  # КЛЮЧ ПОГОДЫ
DEFAULT_CITY = "Moscow"

# ============================================

CITIES_FILE = "user_cities.json"

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
        print(f"Ошибка сохранения: {e}")

def get_user_city(user_id, user_cities):
    return user_cities.get(str(user_id), DEFAULT_CITY)

def set_user_city(user_id, city, user_cities):
    user_cities[str(user_id)] = city
    save_user_cities(user_cities)

# Функция для получения рекомендаций по погоде
def get_weather_advice(temp, description, wind_speed):
    advice = []
    
    # Рекомендации по температуре
    if temp < -20:
        advice.append("🥶 Очень холодно! Надевайте пуховик, шапку-ушанку, шарф, варежки и термобелье. Лучше не выходить без необходимости.")
    elif temp < -10:
        advice.append("🧣 Холодно! Нужен теплый пуховик, шапка, шарф и перчатки. Обувайте теплые сапоги.")
    elif temp < 0:
        advice.append("🧥 Прохладно! Надевайте зимнюю куртку, шапку и шарф. Не забудьте перчатки.")
    elif temp < 10:
        advice.append("🍂 Прохладно. Возьмите демисезонную куртку или пальто. Шарф не помешает.")
    elif temp < 15:
        advice.append("🧥 Прохладно. Лучше надеть легкую куртку или свитер с ветровкой.")
    elif temp < 20:
        advice.append("👕 Тепло. Можно в футболке и джинсах. Вечером может быть прохладно - захватите кофту.")
    elif temp < 25:
        advice.append("☀️ Хорошая погода! Футболка, шорты/джинсы - отлично.")
    elif temp < 30:
        advice.append("🥵 Жарко! Надевайте легкую одежду из натуральных тканей, головной убор обязателен.")
    else:
        advice.append("🥵 Очень жарко! Только легкая одежда, панамка/кепка обязательна. Пейте больше воды!")
    
    # Рекомендации по осадкам
    if 'дождь' in description.lower() or 'ливень' in description.lower():
        advice.append("☔️ Обязательно возьмите зонт! И наденьте непромокаемую обувь.")
    elif 'снег' in description.lower():
        advice.append("❄️ Идет снег. Обувайте непромокаемую обувь, возьмите зонт или капюшон.")
    elif 'гроза' in description.lower():
        advice.append("⚡️ Гроза! По возможности оставайтесь дома. Если выходите, избегайте открытых мест.")
    
    # Рекомендации по ветру
    if wind_speed > 15:
        advice.append("💨 Сильный ветер! Застегнитесь, уберите волосы, будьте осторожны возле домов.")
    elif wind_speed > 8:
        advice.append("🍃 Ветрено. Наденьте ветровку или непродуваемую куртку.")
    
    return "\n".join(advice)

# Создание клавиатуры с кнопками
def get_main_keyboard():
    keyboard = VkKeyboard(one_time=False)  # one_time=False - клавиатура не исчезает
    
    # Первый ряд кнопок
    keyboard.add_button("🌤 Погода сейчас", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📍 Сменить город", color=VkKeyboardColor.SECONDARY)
    
    # Переход на новую строку
    keyboard.add_line()
    
    # Второй ряд
    keyboard.add_button("📅 Прогноз на дату", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🏙 Мой город", color=VkKeyboardColor.SECONDARY)
    
    # Третий ряд
    keyboard.add_line()
    keyboard.add_button("❓ Помощь", color=VkKeyboardColor.POSITIVE)
    
    return keyboard.get_keyboard()

# Клавиатура для смены города
def get_city_keyboard():
    keyboard = VkKeyboard(one_time=True)  # one_time=True - исчезает после нажатия
    
    keyboard.add_button("🌍 Москва", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🌍 Санкт-Петербург", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🌍 Лондон", color=VkKeyboardColor.SECONDARY)
    keyboard.add_button("🌍 Нью-Йорк", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🔙 Вернуться назад", color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

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
            
            # Выбираем эмодзи для погоды
            if 'ясно' in description.lower():
                emoji = "☀️"
            elif 'облач' in description.lower():
                emoji = "☁️"
            elif 'дождь' in description.lower():
                emoji = "🌧"
            elif 'снег' in description.lower():
                emoji = "❄️"
            else:
                emoji = "🌡"
            
            message = f"{emoji} *Погода в {city_name} сейчас:*\n"
            message += f"🌡 Температура: {temp}°C (ощущается {feels_like}°C)\n"
            message += f"📝 {description.capitalize()}\n"
            message += f"💧 Влажность: {humidity}%\n"
            message += f"💨 Ветер: {wind} м/с\n"
            
            # Добавляем рекомендации
            advice = get_weather_advice(temp, description, wind)
            if advice:
                message += f"\n💡 *Совет:*\n{advice}"
            
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
        wind = closest_forecast['wind']['speed']
        
        # Выбираем эмодзи
        if 'ясно' in description.lower():
            emoji = "☀️"
        elif 'облач' in description.lower():
            emoji = "☁️"
        elif 'дождь' in description.lower():
            emoji = "🌧"
        elif 'снег' in description.lower():
            emoji = "❄️"
        else:
            emoji = "🌡"
        
        message = f"{emoji} *Прогноз в {city}*\n"
        message += f"🗓 {forecast_time.strftime('%d.%m.%Y %H:%M')}\n"
        message += f"🌡 {temp}°C (ощущается {feels_like}°C)\n"
        message += f"📝 {description.capitalize()}\n"
        message += f"💨 Ветер: {wind} м/с\n"
        
        # Добавляем рекомендации
        advice = get_weather_advice(temp, description, wind)
        if advice:
            message += f"\n💡 *Совет:*\n{advice}"
        
        return message, True
    except Exception as e:
        return f"❌ Ошибка: {e}", False

def parse_date_time(text):
    now = datetime.now()
    text_lower = text.lower()
    
    # Убираем слова "на", "в", "прогноз" из текста
    text_lower = text_lower.replace('прогноз', '').replace('на', '').replace('в', '').strip()
    
    if 'завтра' in text_lower:
        target_date = now + timedelta(days=1)
        text_lower = text_lower.replace('завтра', '').strip()
    elif 'послезавтра' in text_lower:
        target_date = now + timedelta(days=2)
        text_lower = text_lower.replace('послезавтра', '').strip()
    else:
        target_date = now
    
    hour = 9
    minute = 0
    import re
    
    # Парсим время
    time_match = re.search(r'(\d+)[\s]*[:]?[\s]*(\d*)?', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        if time_match.group(2) and len(time_match.group(2)) > 0:
            minute = int(time_match.group(2))
        # Корректировка для "часов", "утра" и т.д.
        if 'вечера' in text_lower and hour < 12:
            hour += 12
        elif 'дня' in text_lower and hour < 12:
            hour += 12
        elif 'ночи' in text_lower and hour == 12:
            hour = 0
    
    # Парсим дату (день и месяц)
    months = {
        'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
        'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
    }
    for month_name, month_num in months.items():
        if month_name in text_lower:
            day_match = re.search(r'(\d+)', text_lower)
            if day_match:
                day = int(day_match.group(1))
                year = now.year
                if month_num < now.month or (month_num == now.month and day < now.day):
                    year += 1
                target_date = datetime(year, month_num, day)
            break
    
    target_datetime = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_datetime < now:
        target_datetime += timedelta(days=1)
    
    return target_datetime

def send_message(vk, user_id, message, keyboard=None):
    try:
        params = {
            'user_id': user_id,
            'message': message,
            'random_id': 0
        }
        if keyboard:
            params['keyboard'] = keyboard
        vk.messages.send(**params)
        return True
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return False

def start_bot():
    while True:
        try:
            user_cities = load_user_cities()
            print(f"Загружено {len(user_cities)} сохраненных городов")
            vk_session = vk_api.VkApi(token=VK_TOKEN)
            vk = vk_session.get_api()
            longpoll = VkLongPoll(vk_session)
            print("✅ Бот погоды запущен!")
            print("🌍 Город по умолчанию: " + DEFAULT_CITY)
            print("💬 Клавиатура с кнопками активна")
            print("-" * 40)
            
            for event in longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    user_id = event.user_id
                    message_text = event.text.lower().strip()
                    print(f"📨 Получено от {user_id}: {message_text}")
                    current_city = get_user_city(user_id, user_cities)
                    
                    # Обработка кнопок
                    if message_text in ['🌤 погода сейчас', 'погода', 'погода?', 'какая погода', 'weather']:
                        weather, success = get_current_weather(current_city, WEATHER_API_KEY)
                        send_message(vk, user_id, weather, get_main_keyboard())
                    
                    elif message_text in ['📍 сменить город', 'город', 'сменить город']:
                        send_message(vk, user_id, "🌍 Выберите город из списка или напишите 'город Название':", get_city_keyboard())
                    
                    elif message_text in ['🌍 москва', 'москва']:
                        set_user_city(user_id, "Moscow", user_cities)
                        send_message(vk, user_id, f"✅ Город изменен на Москва!", get_main_keyboard())
                    
                    elif message_text in ['🌍 санкт-петербург', 'санкт-петербург', 'спб']:
                        set_user_city(user_id, "Saint Petersburg", user_cities)
                        send_message(vk, user_id, f"✅ Город изменен на Санкт-Петербург!", get_main_keyboard())
                    
                    elif message_text in ['🌍 лондон', 'лондон']:
                        set_user_city(user_id, "London", user_cities)
                        send_message(vk, user_id, f"✅ Город изменен на Лондон!", get_main_keyboard())
                    
                    elif message_text in ['🌍 нью-йорк', 'нью-йорк', 'нью йорк']:
                        set_user_city(user_id, "New York", user_cities)
                        send_message(vk, user_id, f"✅ Город изменен на Нью-Йорк!", get_main_keyboard())
                    
                    elif message_text in ['🏙 мой город', 'мой город', 'текущий город']:
                        send_message(vk, user_id, f"🏙 Ваш текущий город: *{current_city.capitalize()}*", get_main_keyboard())
                    
                    elif message_text.startswith('город '):
                        new_city = message_text.replace('город ', '').strip()
                        weather, success = get_current_weather(new_city, WEATHER_API_KEY)
                        if success:
                            set_user_city(user_id, new_city, user_cities)
                            send_message(vk, user_id, f"✅ Город изменен на {new_city.capitalize()}!", get_main_keyboard())
                        else:
                            send_message(vk, user_id, f"❌ Город '{new_city}' не найден.", get_main_keyboard())
                    
                    elif message_text in ['📅 прогноз на дату', 'прогноз на дату']:
                        send_message(vk, user_id, "📅 Напишите дату и время для прогноза:\n\nПримеры:\n• 9 утра 10 апреля\n• завтра в 15:00\n• послезавтра 8 вечера", get_main_keyboard())
                    
                    elif message_text.startswith('прогноз') or ('утра' in message_text and 'прогноз' not in message_text):
                        try:
                            target_datetime = parse_date_time(message_text)
                            formatted_date = target_datetime.strftime('%d.%m.%Y в %H:%M')
                            send_message(vk, user_id, f"🔍 Ищу прогноз для {current_city} на {formatted_date}...", get_main_keyboard())
                            forecast, success = get_forecast_for_datetime(current_city, WEATHER_API_KEY, target_datetime)
                            send_message(vk, user_id, forecast, get_main_keyboard())
                        except Exception as e:
                            send_message(vk, user_id, f"❌ Не удалось распознать дату.\n\nПримеры:\n• прогноз на 9 утра 10 апреля\n• завтра в 15:00", get_main_keyboard())
                    
                    elif message_text in ['❓ помощь', 'помощь', 'help', 'команды']:
                        help_text = "🤖 *Мои команды:*\n\n"
                        help_text += "🌤 *Погода сейчас* - Текущая погода\n"
                        help_text += "📍 *Сменить город* - Выбрать другой город\n"
                        help_text += "📅 *Прогноз на дату* - Прогноз на конкретное время\n"
                        help_text += "🏙 *Мой город* - Узнать текущий город\n"
                        help_text += "❓ *Помощь* - Показать это сообщение\n\n"
                        help_text += "📝 *Примеры прогнозов:*\n"
                        help_text += "• прогноз на 9 утра 10 апреля\n"
                        help_text += "• завтра в 15:00\n\n"
                        help_text += f"🏙 *Ваш город:* {current_city}"
                        send_message(vk, user_id, help_text, get_main_keyboard())
                    
                    elif message_text in ['🔙 вернуться назад', 'назад', 'меню']:
                        send_message(vk, user_id, "🔙 Главное меню:", get_main_keyboard())
                    
                    elif 'спасибо' in message_text:
                        send_message(vk, user_id, "Всегда пожалуйста! 😊 Обращайтесь за погодой!", get_main_keyboard())
                    
                    elif message_text in ['привет', 'ку', 'здарова', 'hello', 'start']:
                        welcome = f"Привет! 👋\n\nЯ бот погоды с умными советами!\n\n"
                        welcome += f"🌤 *Твой город:* {current_city}\n\n"
                        welcome += "Используй кнопки ниже для управления 👇"
                        send_message(vk, user_id, welcome, get_main_keyboard())
                    
                    else:
                        send_message(vk, user_id, f"❓ Неизвестная команда.\n\nНажмите 'Помощь' для списка команд или используйте кнопки ниже 👇", get_main_keyboard())
                        
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            print("Перезапуск через 10 секунд...")
            time.sleep(10)

if __name__ == "__main__":
    start_bot()
