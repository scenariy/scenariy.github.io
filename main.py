import os
import requests
import json
import re

# Налаштування
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")
wp_user = os.getenv("WP_USER") 
base_url = "http://scenariy.pp.ua/index.php?rest_route="

def generate_and_post():
    # 1. Завантажуємо базу даних
    db = {"topics": {}}
    if os.path.exists("database.json"):
        with open("database.json", "r", encoding="utf-8") as f:
            db = json.load(f)

    print(f"Аналіз теми: {topic}")
    
    # 2. Запит до ШІ для визначення батьківської категорії та контенту
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    Ти - архітектор контенту. Тема: "{topic}".
    1. Визнач основне свято (наприклад, "День матері").
    2. Придумай для нього англійський slug (наприклад, "den-materi").
    3. Напиши детальний сценарій для "{audience}" у форматі HTML (h2, p, li).
    
    Відповідь надай СУВОРО у форматі JSON:
    {{
      "parent_topic": "Назва свята",
      "parent_slug": "slug-svyata",
      "post_title": "Повна назва сценарію",
      "content": "HTML текст сценарію"
    }}
    """
    
    res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    # Очищення відповіді ШІ від можливих маркерів коду
    raw_json = res['candidates'][0]['content']['parts'][0]['text'].replace('```json', '').replace('```', '').strip()
    data = json.loads(raw_json)

    # 3. Робота з базою: чи є вже таке свято?
    parent_slug = db["topics"].get(data["parent_topic"], data["parent_slug"])
    
    # Отримуємо ID категорії в WP або створюємо її (спрощено - використовуємо slug)
    print(f"Свято: {data['parent_topic']} -> /{parent_slug}/")

    # 4. Публікація сценарію
    auth = (wp_user, wp_password)
    
    # Генеруємо унікальне підпосилання: /den-materi/scenariy-N
    # Для простоти додаємо timestamp, щоб не було дублів
    import time
    sub_slug = f"scenariy-{int(time.time())}"

    post_data = {
        "title": data["post_title"],
        "content": f"<h1>{data['post_title']}</h1>" + data["content"], # Фікс (no title)
        "slug": sub_slug,
        "status": "publish"
    }

    # Надсилаємо пост
    wp_res = requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    if wp_res.status_code == 201:
        # Оновлюємо базу, якщо свято нове
        if data["parent_topic"] not in db["topics"]:
            db["topics"][data["parent_topic"]] = data["parent_slug"]
            with open("database.json", "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Готово! Сценарій додано до розділу {data['parent_topic']}")
        print(f"URL: http://scenariy.pp.ua/{parent_slug}/{sub_slug}/")
    else:
        print(f"❌ Помилка WP: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
