import os
import requests
import json
import re
import time

# Налаштування
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")
wp_user = os.getenv("WP_USER") 
base_url = "http://scenariy.pp.ua/index.php?rest_route="

def generate_and_post():
    db = {"topics": {}}
    if os.path.exists("database.json"):
        with open("database.json", "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
            except:
                db = {"topics": {}}

    print(f"Аналіз теми: {topic}")
    
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    # Покращений промпт для красивого оформлення
    prompt = f"""
    Ти - професійний веб-дизайнер сценаріїв. Тема: "{topic}".
    1. Основне свято (напр. "8 березня").
    2. Англійський slug (напр. "8-bereznya").
    3. Сценарій для "{audience}".

    ВИМОГИ ДО ОФОРМЛЕННЯ:
    - Використовуй <h2> для розділів.
    - Використовуй <p> та <ul>/<li>.
    - Додавай кольори через <span style="color: #e91e63;">важливі фрази</span> (використовуй різні приємні кольори для акцентів).
    - НЕ ПИШИ назву сценарію всередині блоку content, почни одразу з мети чи вступу.

    Відповідь СУВОРО JSON:
    {{
      "parent_topic": "Назва свята",
      "parent_slug": "slug-svyata",
      "post_title": "Повна назва сценарію",
      "content": "HTML текст сценарію БЕЗ ЗАГОЛОВКА"
    }}
    """
    
    res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    raw_text = res['candidates'][0]['content']['parts'][0]['text']
    raw_json = re.sub(r'```json|```', '', raw_text).strip()
    data = json.loads(raw_json)

    parent_slug = db["topics"].get(data["parent_topic"], data["parent_slug"])

    auth = (wp_user, wp_password)
    sub_slug = f"scenariy-{int(time.time())}"

    # ФОРМУЄМО КОНТЕНТ: Один заголовок зверху + стилізований текст
    styled_title = f"<h1 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;'>{data['post_title']}</h1>"
    full_html = styled_title + data["content"]

    post_data = {
        "title": data["post_title"],
        "content": full_html,
        "slug": sub_slug,
        "status": "publish"
    }

    print(f"Публікація: {data['post_title']}")
    wp_res = requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    if wp_res.status_code == 201:
        if data["parent_topic"] not in db["topics"]:
            db["topics"][data["parent_topic"]] = data["parent_slug"]
            with open("database.json", "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Успіх! URL: http://scenariy.pp.ua/{sub_slug}/")
    else:
        print(f"❌ Помилка: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
