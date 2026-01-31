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
    # 1. Завантаження бази
    db = {"topics": {}}
    if os.path.exists("database.json"):
        with open("database.json", "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = {"topics": {}}

    print(f"Робота над темою: {topic}")
    
    # 2. Промпт для ШІ (тільки контент)
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    Напиши сценарій для: {topic} (Аудиторія: {audience}).
    Відповідь надай суворо в JSON:
    {{
      "category_name": "Головне свято (напр. 8 Березня)",
      "category_slug": "slug-latynoyu",
      "post_title": "Красива назва сценарію",
      "intro": "Короткий вступ (1-2 речення)",
      "roles": "Список ролей (якщо є, HTML li)",
      "main_script": "Основний хід подій (HTML p, li)",
      "conclusion": "Фінал"
    }}
    """
    
    res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    raw_json = re.sub(r'```json|```', '', res['candidates'][0]['content']['parts'][0]['text']).strip()
    data = json.loads(raw_json)

    # 3. Логіка бази (як ти просив)
    c_slug = data["category_slug"]
    if c_slug not in db["topics"]:
        db["topics"][c_slug] = []
    
    scenario_index = len(db["topics"][c_slug]) + 1
    db["topics"][c_slug].append(scenario_index)
    
    # Створюємо посилання типу /8-bereznya-scenariy-1
    final_post_slug = f"{c_slug}-scenariy-{scenario_index}"

    # 4. НАШ ЖОРСТКИЙ ШАБЛОН ДИЗАЙНУ
    html_template = f"""
    <div style="font-family: 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: auto; border: 1px solid #eee; padding: 30px; border-radius: 10px; background: #fff;">
        <div style="text-align: center; border-bottom: 3px solid #f1c40f; padding-bottom: 20px; margin-bottom: 20px;">
            <span style="background: #f1c40f; color: #fff; padding: 5px 15px; border-radius: 20px; font-size: 14px; text-transform: uppercase;">{data['category_name']}</span>
            <h1 style="color: #2c3e50; margin-top: 15px;">{data['post_title']}</h1>
            <p style="font-style: italic; color: #7f8c8d;">Для аудиторії: {audience}</p>
        </div>
        
        <div style="background: #fef9e7; padding: 15px; border-left: 5px solid #f1c40f; margin-bottom: 25px;">
            <strong>Вступ:</strong> {data['intro']}
        </div>

        <h3 style="color: #d35400;">🎭 Дійові особи:</h3>
        <ul>{data['roles']}</ul>

        <h3 style="color: #2980b9;">📜 Хід заходу:</h3>
        <div style="background: #fafafa; padding: 20px; border-radius: 5px;">{data['main_script']}</div>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px dashed #ccc; text-align: center; color: #95a5a6;">
            {data['conclusion']}
        </div>
    </div>
    """

    # 5. Публікація
    post_data = {
        "title": data["post_title"],
        "content": html_template,
        "slug": final_post_slug,
        "status": "publish"
    }

    auth = (wp_user, wp_password)
    requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    # Зберігаємо базу
    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✅ Опубліковано: {final_post_slug}")

if __name__ == "__main__":
    generate_and_post()
