import os
import requests
import json
import re

# Налаштування
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")
wp_user = "4731017_wpresse934f6d9" 
wp_url = "http://scenariy.pp.ua/index.php?rest_route=/wp/v2/posts"

def clean_content(text):
    # Видаляємо сміття типу ```html або зайві маркувальні знаки
    text = re.sub(r'```html', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def generate_and_post():
    print(f"Генеруємо сценарій для: {topic}...")
    
    # ПЕРЕВІР ЦЕЙ РЯДОК: тут не має бути квадратних дужок навколо https
    gen_url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=){gemini_key}"
    
    prompt = f"""
    Ти - професійний сценарист та SEO-спеціаліст.
    Напиши детальний сценарій заходу на тему: {topic}. 
    Аудиторія: {audience}. Мова: Українська. 
    Оформи як HTML (використовуй h2, p, ul, li).
    
    В самому кінці відповіді додай рядок: 
    SLUG: [тут напиши коротке англійське посилання для цієї теми, наприклад den-kozatstva]
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    # Виконуємо запит
    response = requests.post(gen_url, json=payload)
    res_data = response.json()
    
    if response.status_code != 200:
        print(f"❌ Помилка Gemini: {res_data}")
        return

    raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
    
    # Шукаємо SLUG в тексті
    slug = "scenario"
    if "SLUG:" in raw_text:
        parts = raw_text.split("SLUG:")
        main_text = parts[0]
        slug = parts[1].strip().replace("[", "").replace("]", "").lower()
        slug = re.sub(r'[^a-z0-9\-]', '', slug) # Залишаємо тільки латиницю і дефіси
    else:
        main_text = raw_text

    full_content = clean_content(main_text)

    # Публікація в WordPress
    auth = (wp_user, wp_password)
    post_data = {
        "title": topic, # Назва заходу
        "content": full_content,
        "slug": slug,   # SEO посилання англійською
        "status": "publish"
    }

    print(f"Надсилаємо в WordPress... Посилання буде: [http://scenariy.pp.ua/](http://scenariy.pp.ua/){slug}/")
    wp_res = requests.post(wp_url, auth=auth, json=post_data)

    if wp_res.status_code == 201:
        print(f"✅ Успіх! Сценарій опубліковано.")
    else:
        print(f"❌ Помилка WP: {wp_res.status_code}")
        print(wp_res.text)

if __name__ == "__main__":
    generate_and_post()
