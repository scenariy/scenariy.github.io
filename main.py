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
    # 1. Завантаження бази даних
    db = {"topics": {}}
    if os.path.exists("database.json"):
        with open("database.json", "r", encoding="utf-8") as f:
            try: db = json.load(f)
            except: db = {"topics": {}}

    print(f"Обробка теми: {topic}")
    
    # 2. Промпт для ШІ
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    Ти - професійний сценарист. Напиши сценарій для: {topic} (Аудиторія: {audience}).
    Відповідь надай суворо в JSON:
    {{
      "category_name": "Назва свята (напр. 8 Березня)",
      "category_slug": "slug-latynoyu",
      "post_title": "Оригінальна назва сценарію",
      "intro": "Вступ (1-2 речення)",
      "roles": "Дійові особи (HTML li)",
      "main_script": "Хід подій (HTML p, li)",
      "conclusion": "Фінал"
    }}
    """
    
    res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    raw_json = re.sub(r'```json|```', '', res['candidates'][0]['content']['parts'][0]['text']).strip()
    data = json.loads(raw_json)

    # 3. Логіка бази та посилань
    c_slug = data["category_slug"]
    if c_slug not in db["topics"]:
        db["topics"][c_slug] = []
    
    scenario_num = len(db["topics"][c_slug]) + 1
    db["topics"][c_slug].append(scenario_num)
    
    final_post_slug = f"{c_slug}-scenariy-{scenario_num}"

    # 4. ВІДКОРИГОВАНИЙ ШАБЛОН (БЕЗ ДУБЛЮВАННЯ НАЗВИ)
    html_template = f"""
    <div style="font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #e0e0e0; max-width: 850px; margin: 20px auto; border: 1px solid #333; padding: 40px; border-radius: 12px; background: #1a1a1a; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
        
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="background: #f1c40f; color: #000; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">
                {data['category_name']}
            </span>
            <p style="margin-top: 15px; font-style: italic; color: #aaa; font-size: 16px;">Призначено для: {audience}</p>
        </div>
        
        <div style="background: rgba(241, 196, 15, 0.1); padding: 20px; border-left: 4px solid #f1c40f; margin-bottom: 30px; border-radius: 4px;">
            <strong style="color: #f1c40f;">Вступ:</strong> <span style="color: #ccc;">{data['intro']}</span>
        </div>

        <div style="margin-bottom: 30px;">
            <h3 style="color: #f39c12; border-bottom: 1px solid #333; padding-bottom: 10px; display: flex; align-items: center;">🎭 Дійові особи</h3>
            <ul style="list-style-type: none; padding-left: 10px; color: #bbb;">{data['roles']}</ul>
        </div>

        <div style="margin-bottom: 30px;">
            <h3 style="color: #3498db; border-bottom: 1px solid #333; padding-bottom: 10px;">📜 Хід заходу</h3>
            <div style="color: #ddd; line-height: 1.8;">{data['main_script']}</div>
        </div>

        <div style="margin-top: 40px; padding: 20px; border-top: 1px solid #333; text-align: center; color: #777; font-size: 14px;">
            {data['conclusion']}
        </div>
    </div>
    """

    # 5. Публікація (Фікс для заголовка)
    post_data = {
        "title": data["post_title"],
        "content": html_template,
        "slug": final_post_slug,
        "status": "publish"
    }

    auth = (wp_user, wp_password)
    # Спеціальний заголовок для авторизації, щоб WP точно прийняв title
    wp_res = requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    if wp_res.status_code == 201:
        # Оновлюємо базу тільки при успіху
        with open("database.json", "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print(f"✅ Готово: http://scenariy.pp.ua/{final_post_slug}/")
    else:
        print(f"❌ Помилка: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
