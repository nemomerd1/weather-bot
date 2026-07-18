import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# --- НАСТРОЙКИ ---
EMAIL_FROM = 'merckuschevdaniil@yandex.ru'
EMAIL_TO = 'merckuschevdaniil@yandex.ru'
DEFAULT_CITY = 'Yelabuga'
APP_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# --- 1. ПОЛУЧЕНИЕ ПОГОДЫ (подробный прогноз) ---
def get_weather_report(city_query):
    try:
        # Ищем координаты
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_query}&count=1&language=ru"
        geo_data = requests.get(geo_url).json()
        
        if "results" not in geo_data:
            return None, f"Город '{city_query}' не найден."
        
        city_name = geo_data["results"][0]["name"]
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        # Получаем почасовой прогноз на 24 часа
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation_probability,weathercode,cloudcover&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&current_weather=true&timezone=auto"
        weather_data = requests.get(weather_url).json()
        
        current = weather_data["current_weather"]
        hourly = weather_data["hourly"]
        daily = weather_data["daily"]
        
        # Текущая температура
        temp = current["temperature"]
        
        # Прогноз на день
        max_temp = daily["temperature_2m_max"][0]
        min_temp = daily["temperature_2m_min"][0]
        daily_precip = daily["precipitation_sum"][0]
        
        # Анализируем почасовой прогноз
        hourly_forecast = []
        will_rain = False
        rain_hours = []
        
        # Берем следующие 24 часа
        current_hour = current["time"][:13]  # "2024-01-15T10"
        
        for i in range(24):
            hour_time = hourly["time"][i]
            hour_temp = hourly["temperature_2m"][i]
            hour_precip = hourly["precipitation_probability"][i]
            hour_clouds = hourly["cloudcover"][i]
            hour_code = hourly["weathercode"][i]
            
            # Извлекаем час (10, 11, 12...)
            hour_num = hour_time[11:13]
            
            # Определяем состояние погоды
            weather_desc = get_weather_description(hour_code, hour_clouds)
            
            # Проверяем дождь
            if hour_precip > 50 or hour_code in [51, 53, 55, 61, 63, 65]:
                will_rain = True
                rain_hours.append(f"{hour_num}:00")
            
            hourly_forecast.append({
                'hour': hour_num,
                'temp': hour_temp,
                'precip': hour_precip,
                'desc': weather_desc
            })
        
        # Формируем текст письма
        subject = f"🌤 Прогноз погоды: {city_name}"
        
        body = f"""
☀️ ПОГОДА В ГОРОДЕ {city_name.upper()}

📊 ОБЩАЯ ИНФОРМАЦИЯ НА СЕГОДНЯ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌡️  Сейчас: {temp}°C
📈 Макс: {max_temp}°C | 📉 Мин: {min_temp}°C
💧 Осадки за день: {daily_precip} мм
"""
        
        if will_rain:
            body += f"\n⚠️  БУДЕТ ДОЖДЬ! (в {', '.join(rain_hours[:3])})\n"
        else:
            body += "\n✅ Дождя не ожидается\n"
        
        body += "\n🕐 ПРОГНОЗ ПО ЧАСАМ (следующие 12 часов):\n"
        body += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for hour_data in hourly_forecast:
            rain_icon = "🌧️" if hour_data['precip'] > 50 else "☀️"
            body += f"{hour_data['hour']}:00 | {hour_data['temp']:>3}°C | {hour_data['precip']:>3}% {rain_icon} | {hour_data['desc']}\n"
        
        body += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        body += "Хорошего дня! 🌟"
        
        return subject, body
        
    except Exception as e:
        return None, f"Ошибка при получении данных: {e}"

# --- 2. ОПИСАНИЕ ПОГОДЫ ---
def get_weather_description(code, cloudcover):
    # WMO Weather interpretation codes
    if code == 0:
        return "Ясно ☀️"
    elif code in [1, 2]:
        if cloudcover < 30:
            return "Преимущественно ясно 🌤️"
        else:
            return "Переменная облачность ⛅"
    elif code == 3:
        return "Пасмурно ☁️"
    elif code in [45, 48]:
        return "Туман 🌫️"
    elif code in [51, 53, 55]:
        return "Морось 🌦️"
    elif code in [61, 63, 65]:
        return "Дождь ️"
    elif code in [71, 73, 75]:
        return "Снег ❄️"
    elif code in [80, 81, 82]:
        return "Ливень ⛈️"
    elif code in [95, 96, 99]:
        return "Гроза "
    else:
        return "Неизвестно"

# --- 3. ОТПРАВКА ПИСЬМА ---
def send_email_report(subject, body):
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as server:
            server.login(EMAIL_FROM, APP_PASSWORD)
            server.send_message(msg)
        print("✅ Письмо успешно отправлено!")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# --- 4. ЗАПУСК ---
if __name__ == "__main__":
    print("🔄 Получаем подробный прогноз...")
    subject, body = get_weather_report(DEFAULT_CITY)
    
    if subject:
        send_email_report(subject, body)
    else:
        print(body)  # Это ошибка
