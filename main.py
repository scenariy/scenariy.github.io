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
wp_url = "[http://scenariy.pp.ua/index.php?rest_route=/wp/v2/posts](http://scenariy.pp.ua/index.php?rest_route=/wp/v2/posts)"

def clean_html(text):
    # Видаляємо маркер ```html та ```
    text = re.sub(r'```html', '', text)
    text = re.sub(r'```', '', text)
    return text.strip()

def generate_and_post():
    # 1. Запит до Gemini для генерації контенту та SEO-даних
    gen_url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=){gemini_key}"
    
    # Просимо ШІ повернути сценарій ТА технічні дані (slug)
    prompt = f"""
    Напиши детальний сценарій заходу на тему: {topic}. 
    Аудиторія: {audience}. Мова: Українська. 
    Оформи як HTML (h2, p, ul, li).
    
    Також придумай коротке SEO-посилання (slug) для цієї теми англійською мовою (наприклад: den-kozatstva).
    Відповідь почни з тегу [SLUG:твоє_посилання], а потім іди сам текст сценарію.
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(gen_url, json=payload).json()
    
    raw_text = res['candidates'][0]['content']['parts'][0]['text']
    
    # Витягуємо SLUG за допомогою регулярки
    slug_match = re.search(r'\[SLUG:(.*?)\]', raw_text)
    slug = slug_match.group(1).strip() if slug_match else "scenario"
    
    # Очищаємо основний текст
    full_content = clean_html(raw_text.replace(f"[SLUG:{slug}]", ""))

    # 2. Публікація в WordPress
    auth = (wp_user, wp_password)
    post_data = {
        "title": f"Сценарій: {topic}",
        "content": full_content,
        "slug": slug, # Це виправить посилання на англійське
        "status": "publish"
    }

    print(f"Публікуємо з посиланням: {slug}...")
    wp_res = requests.post(wp_url, auth=auth, json=post_data)

    if wp_res.status_code == 201:
        print(f"✅ Успіх! [http://scenariy.pp.ua/](http://scenariy.pp.ua/){slug}/")
    else:
        print(f"❌ Помилка: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
