import os
import requests
from google import genai

# 1. Отримуємо змінні
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")

wp_user = "4731017_wpresse934f6d9" 
wp_url = "http://scenariy.pp.ua/wp-json/wp/v2/posts"

def generate_and_post():
    # 2. Новий спосіб ініціалізації клієнта
    client = genai.Client(api_key=gemini_key)
    
    prompt = f"Напиши детальний HTML-сценарій для заходу: {topic}. Аудиторія: {audience}. Мова: Українська."

    print(f"Генеруємо сценарій...")
    # Використовуємо стабільну модель 1.5-flash
    response = client.models.generate_content(
        model="gemini-1.5-flash", 
        contents=prompt
    )
    
    content_html = response.text

    # 3. Публікація
    auth = (wp_user, wp_password)
    post_data = {
        "title": f"Сценарій: {topic}",
        "content": content_html,
        "status": "publish"
    }

    print("Надсилаємо в WordPress...")
    res = requests.post(wp_url, auth=auth, json=post_data)

    if res.status_code == 201:
        print("✅ Готово! Перевіряй сайт.")
    else:
        print(f"❌ Помилка WP: {res.status_code} - {res.text}")

if __name__ == "__main__":
    generate_and_post()
