import os
import requests
import smtplib
from email.message import EmailMessage

# --- НАСТРОЙКИ ---
EMAIL_FROM = 'merckuschevdaniil@yandex.ru'   # <-- ВПИШИ СЮДА СВОЮ ПОЧТУ
EMAIL_TO = 'merckuschevdaniil@yandex.ru'     # <-- И СЮДА
DEFAULT_CITY = 'Yelabuga'

# Пароль берется из настроек GitHub (мы его спрятали на Шаге 1)
APP_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# --- 1. ПОЛУЧЕНИЕ ПОГОДЫ ---
def get_weather_report(city_query):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_query}&count=1&language=ru"
        geo_data = requests.get(geo_url).json()
        
        if "results" not in geo_data:
            return f"Город '{city_query}' не найден."
        
        city_name = geo_data["results"][0]["name"]
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_data = requests.get(weather_url).json()
        
        temp = weather_data["current_weather"]["temperature"]
        wind = weather_data["current_weather"]["windspeed"]
        
        return f" Погода в городе {city_name}\n Температура: {temp}°C\n💨 Ветер: {wind} км/ч"
    except Exception as e:
        return f"Ошибка при получении данных: {e}"

# --- 2. ОТПРАВКА ПИСЬМА ---
def send_email_report(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL('smtp.yandex.ru', 465) as server:
            server.login(EMAIL_FROM, APP_PASSWORD)
            server.send_message(msg)
        print("✅ Письмо успешно отправлено!")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

# --- 3. ЗАПУСК ---
if __name__ == "__main__":
    print("🔄 Проверяем погоду...")
    weather_text = get_weather_report(DEFAULT_CITY)
    full_message = f"️ Доброе утро!\n\n{weather_text}\n\nХорошего дня!"
    send_email_report("🌤 Ваш утренний прогноз", full_message)
