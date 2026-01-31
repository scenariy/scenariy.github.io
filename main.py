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

    print(f"Аналіз теми: {topic}")
    
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    # Нова структура промпту: розділяємо дані
    prompt = f"""
    Ти - професійний сценарист. Напиши сценарій на тему: "{topic}" для "{audience}".
    
    СТРУКТУРА ВІДПОВІДІ:
    1. Спочатку напиши технічний блок у форматі JSON:
    {{
      "parent_topic": "Назва свята",
      "parent_slug": "slug-svyata",
      "post_title": "Повна назва сценарію"
    }}
    
    2. Потім напиши блок [CONTENT] і після нього детальний сценарій в HTML (h2, p, ul, li) з використанням <span style="color: #hex;"> для кольорових акцентів.
    """
    
    res = requests.post(gen_url, json={"contents": [{"parts": [{"text": prompt}]}]}).json()
    full_response = res['candidates'][0]['content']['parts'][0]['text']

    # Парсимо технічні дані (JSON)
    try:
        json_part = re.search(r'\{.*\}', full_response, re.DOTALL).group()
        data = json.loads(json_part)
    except Exception as e:
        print(f"❌ Помилка JSON: {e}")
        return

    # Парсимо контент (все, що після [CONTENT])
    if "[CONTENT]" in full_response:
        content_html = full_response.split("[CONTENT]")[1].strip()
    else:
        content_html = full_response.split("}")[1].strip()

    # Очищуємо від можливих залишків Markdown
    content_html = re.sub(r'```html|```', '', content_html).strip()

    parent_slug = db["topics"].get(data["parent_topic"], data["parent_slug"])
    sub_slug = f"scenariy-{int(time.time())}"

    # Красиве оформлення заголовка (вирішуємо проблему no title)
    styled_header = f"""
    <div style="border-left: 5px solid #3498db; padding: 15px; background: #f8f9fa; margin-bottom: 25px;">
        <h1 style="color: #2c3e50; margin: 0; font-size: 28px;">{data['post_title']}</h1>
        <small style="color: #7f8c8d;">Категорія: {data['parent_topic']} | Для: {audience}</small>
    </div>
    """
    
    full_payload = styled_header + content_html

    post_data = {
        "title": data["post_title"],
        "content": full_payload,
        "slug": sub_slug,
        "status": "publish"
    }

    print(f"Надсилаємо в WordPress: {data['post_title']}")
    auth = (wp_user, wp_password)
    wp_res = requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    if wp_res.status_code == 201:
        if data["parent_topic"] not in db["topics"]:
            db["topics"][data["parent_topic"]] = data["parent_slug"]
            with open("database.json", "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)
        print(f"✅ Готово! http://scenariy.pp.ua/{sub_slug}/")
    else:
        print(f"❌ WP Error: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
