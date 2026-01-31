import os
import requests
import google.generativeai as genai

# 1. Отримуємо змінні з GitHub Actions
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")

# Твій логін у WordPress (той самий, під яким заходиш в адмінку)
wp_user = "4731017_wpresse934f6d9" 
wp_url = "http://scenariy.pp.ua/wp-json/wp/v2/posts"

def generate_and_post():
    # 2. Налаштування Gemini
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Швидка версія
    
    prompt = f"""
    Напиши детальний, цікавий сценарій для шкільного чи позашкільного заходу.
    Тема: {topic}
    Цільова аудиторія: {audience}
    Мова: Українська.
    Структура: Вступ, основна частина з ролями, заключення.
    Оформ текст у стилі HTML (використовуй <h2>, <p>, <ul>, <li>), щоб він гарно виглядав на сайті.
    """

    print(f"Генеруємо сценарій на тему: {topic}...")
    response = model.generate_content(prompt)
    content_html = response.text

    # 3. Публікація в WordPress
    auth = (wp_user, wp_password)
    
    post_data = {
        "title": f"Сценарій: {topic} ({audience})",
        "content": content_html,
        "status": "publish" # Запис одразу з'явиться на сайті
    }

    print("Відправляємо на сайт...")
    res = requests.post(wp_url, auth=auth, json=post_data)

    if res.status_code == 201:
        print("✅ Успіх! Сценарій опубліковано на scenariy.pp.ua")
    else:
        print(f"❌ Помилка публікації: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    if not topic or not gemini_key:
        print("❌ Помилка: Тема або API ключ відсутні!")
    else:
        generate_and_post()
