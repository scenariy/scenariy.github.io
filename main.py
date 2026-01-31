import os
import requests
import json

# 1. Отримання даних з оточення GitHub Actions
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")

# Налаштування твого сайту
wp_user = "4731017_wpresse934f6d9" 
wp_url = "http://scenariy.pp.ua/wp-json/wp/v2/posts"

def generate_and_post():
    print(f"Генеруємо сценарій за допомогою Gemini 2.0 Flash для теми: {topic}...")
    
    # ПРЯМИЙ URL ДО МОДЕЛІ 2.0 FLASH
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    prompt = f"Напиши детальний сценарій заходу на тему: {topic}. Аудиторія: {audience}. Мова: Українська. Оформи як HTML (використовуй <h2>, <p>, <ul>, <li>)."
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}
    
    # Запит до штучного інтелекту
    response = requests.post(gen_url, headers=headers, data=json.dumps(payload))
    res_data = response.json()
    
    if response.status_code != 200:
        print(f"❌ Помилка Gemini: {res_data}")
        return

    # Отримання тексту сценарію
    try:
        content_html = res_data['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        print("❌ Не вдалося отримати текст з відповіді AI")
        return

    # 3. Публікація в WordPress
    auth = (wp_user, wp_password)
    post_data = {
        "title": f"Сценарій: {topic}",
        "content": content_html,
        "status": "publish"
    }

    print("Надсилаємо результат на WordPress...")
    res = requests.post(wp_url, auth=auth, json=post_data)

    if res.status_code == 201:
        print("✅ Успіх! Сценарій опубліковано на сайті scenariy.pp.ua")
    else:
        print(f"❌ Помилка WordPress: {res.status_code} - {res.text}")

if __name__ == "__main__":
    if not gemini_key:
        print("❌ Помилка: Відсутній GEMINI_API_KEY у секретах GitHub")
    else:
        generate_and_post()
