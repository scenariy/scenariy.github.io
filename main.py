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
    text = re.sub(r'```html', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def generate_and_post():
    print(f"Генеруємо сценарій для: {topic}...")
    
    # Очищуємо URL від можливих лінків/дужок, які додає редактор
    raw_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    gen_url = raw_url.replace('[', '').replace(']', '').replace('(', '').replace(')', '').strip()
    
    prompt = f"""
    Ти - професійний сценарист. Напиши детальний сценарій заходу на тему: {topic}. 
    Аудиторія: {audience}. Мова: Українська. 
    Оформи як HTML (h2, p, ul, li).
    
    В самому кінці відповіді додай рядок: 
    SLUG: [тут напиши англійське посилання для цієї теми латиницею]
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(gen_url, json=payload)
        response.raise_for_status()
        res_data = response.json()
    except Exception as e:
        print(f"❌ Помилка запиту до Gemini: {e}")
        return

    raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
    
    # Шукаємо SLUG
    slug = "scenario"
    if "SLUG:" in raw_text:
        parts = raw_text.split("SLUG:")
        main_text = parts[0]
        slug_raw = parts[1].strip().split('\n')[0]
        slug = re.sub(r'[^a-z0-9\-]', '', slug_raw.lower())
    else:
        main_text = raw_text

    full_content = clean_content(main_text)

    # Публікація в WordPress
    auth = (wp_user, wp_password)
    post_data = {
        "title": topic,
        "content": full_content,
        "slug": slug,
        "status": "publish"
    }

    print(f"Надсилаємо в WordPress... Slug: {slug}")
    wp_res = requests.post(wp_url, auth=auth, json=post_data)

    if wp_res.status_code == 201:
        print(f"✅ Успіх! http://scenariy.pp.ua/{slug}/")
    else:
        print(f"❌ Помилка WP: {wp_res.status_code} - {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
