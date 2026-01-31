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
            try: db = json.load(f)
            except: db = {"topics": {}}

    print(f"Генерація сценарію: {topic}")
    
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    prompt = f"""
    Напиши професійний сценарій: {topic} (Аудиторія: {audience}).
    Відповідь СУВОРО JSON:
    {{
      "category_name": "Назва свята",
      "category_slug": "slug-latynoyu",
      "post_title": "Красива назва",
      "intro": "Вступ (без заголовка 'Вступ')",
      "roles": "Список li",
      "main_script": "Хід подій HTML (p, li, h4)",
      "conclusion": "Фінал"
    }}
    """
    
    res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    raw_json = re.sub(r'```json|```', '', res['candidates'][0]['content']['parts'][0]['text']).strip()
    data = json.loads(raw_json)

    # Логіка бази
    c_slug = data["category_slug"]
    if c_slug not in db["topics"]:
        db["topics"][c_slug] = []
    
    scenario_num = len(db["topics"][c_slug]) + 1
    db["topics"][c_slug].append(scenario_num)
    final_post_slug = f"{c_slug}-scenariy-{scenario_num}"

    # НОВИЙ ТЕМНИЙ ДИЗАЙН (Fixed UI)
    # Ми використовуємо вбудовані стилі, які ігнорують налаштування браузера
    html_template = f"""
    <div style="background-color: #121212 !important; color: #e0e0e0 !important; font-family: 'Inter', sans-serif; padding: 40px; border-radius: 16px; border: 1px solid #333; max-width: 800px; margin: 20px auto; box-shadow: 0 20px 40px rgba(0,0,0,0.4);">
        
        <div style="text-align: center; margin-bottom: 35px;">
            <div style="display: inline-block; background: #FFD700; color: #000; padding: 5px 15px; border-radius: 6px; font-size: 12px; font-weight: 800; text-transform: uppercase; margin-bottom: 15px;">
                {data['category_name']}
            </div>
            <p style="color: #888; font-size: 14px; margin: 0;">Цільова аудиторія: {audience}</p>
        </div>

        <div style="background: #1e1e1e; padding: 20px; border-left: 4px solid #FFD700; border-radius: 4px; margin-bottom: 30px;">
            <p style="margin: 0; line-height: 1.6; color: #bbb;">{data['intro']}</p>
        </div>

        <div style="margin-bottom: 40px;">
            <h3 style="color: #FFD700; font-size: 20px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;">🎭 Дійові особи</h3>
            <ul style="color: #ccc; line-height: 1.8;">{data['roles']}</ul>
        </div>

        <div style="margin-bottom: 40px;">
            <h3 style="color: #4da6ff; font-size: 20px; border-bottom: 1px solid #333; padding-bottom: 10px; margin-bottom: 20px;">📜 Сценарій заходу</h3>
            <div style="color: #ddd; line-height: 1.9;">{data['main_script']}</div>
        </div>

        <div style="text-align: center; color: #666; font-style: italic; border-top: 1px solid #222; padding-top: 20px;">
            {data['conclusion']}
        </div>
    </div>
    """

    post_data = {
        "title": data["post_title"],
        "content": html_template,
        "slug": final_post_slug,
        "status": "publish"
    }

    auth = (wp_user, wp_password)
    wp_res = requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    if wp_res.status_code == 201:
        with open("database.json", "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print(f"✅ Успіх! http://scenariy.pp.ua/{final_post_slug}/")
    else:
        print(f"❌ Помилка: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
