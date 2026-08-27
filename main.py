import os
import requests
import json
import time

topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
wishes = os.getenv("WISHES", "")
gemini_key = os.getenv("GEMINI_API_KEY")

def generate_and_save():
    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        attempt += 1
        print(f"🔄 Спроба {attempt} із {max_retries}...")
        
        try:
            db = {"topics": {}}
            if os.path.exists("database.json"):
                with open("database.json", "r", encoding="utf-8") as f:
                    try:
                        db = json.load(f)
                        if "topics" not in db: db = {"topics": {}}
                    except Exception:
                        db = {"topics": {}}

            existing_slugs = list(db["topics"].keys())
            
            gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
            
            prompt = f"""
            Ти - SEO-експерт та архітектор контенту. 
            Твоє завдання: класифікувати захід "{topic}" та написати сценарій для "{audience}". Враховуючи вік та можливості аудиторії, а також масштаби.
        
            ОСОБЛИВІ ПОБАЖАННЯ КОРИСТУВАЧА:
            "{wishes}"
            
            КРОК 1: АНАЛІЗ КАТЕГОРІЇ
            - Перевір існуючі категорії: {existing_slugs}.
            - Якщо тема "{topic}" схожа на існуючу, ОБОВ'ЯЗКОВО використай її slug.
            - Якщо тема НОВА: не перекладай назву дослівно. Знайди офіційну міжнародну назву англійською (наприклад "international-womens-day").
        
            КРОК 2: ПРАВИЛА ГЕНЕРАЦІЇ КОНТЕНТУ
            1. МУЗИКА: "Мелодія: [назва]" + додавай блок <details><summary>🎵 Підбірка музики</summary><ul>...</ul></details>. Світова класика чи сучасна українська музика.
            2. ВІРШІ ТА ПІСНІ: Повний текст у блоці <details><summary>📜 Текст вірша/пісні</summary>...</details>.
            3. ІНТЕРАКТИВ: Повний опис у блоці <details><summary>🥇 Повний опис конкурсу</summary>...</details>.
        
            Відповідь СУВОРО JSON:
            {{
              "category_name": "Офіційна повна назва свята українською",
              "category_slug": "international-standard-slug",
              "post_title": "Красива назва сценарію",
              "seo_description": "Короткий опис сценарію (2-3 речення)",
              "intro": "Вступ",
              "roles": "Список li без ul",
              "main_script": "Хід подій HTML (p, li, h4)",
              "conclusion": "Фінал"
            }}
            """ 

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.7
                }
            }
            
            res = requests.post(gen_url, json=payload).json()
            if 'candidates' not in res:
                raise ValueError(f"API Gemini повернув помилку: {res}")

            raw_response = res['candidates'][0]['content']['parts'][0]['text']
            start_index = raw_response.find('{')
            end_index = raw_response.rfind('}') + 1
            clean_json = raw_response[start_index:end_index]
            data = json.loads(clean_json, strict=False)

            if isinstance(data, list):
                data = data[0]

            c_slug = data["category_slug"]
            if c_slug not in db["topics"]:
                db["topics"][c_slug] = {
                    "name": data["category_name"],
                    "scenarios": []
                }
            
            scenario_num = len(db["topics"][c_slug]["scenarios"]) + 1
            final_slug = f"{c_slug}-scenariy-{scenario_num}"
            file_name = f"{final_slug}.html"

            page_html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['post_title']} — Сценарій</title>
    <meta name="description" content="{data.get('seo_description', '')}">
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header class="header">
            <a href="/" class="back-link">← На головну</a>
            <div class="badge">{data['category_name']}</div>
            <h1>{data['post_title']}</h1>
            <p class="subtitle">Для аудиторії: {audience}</p>
        </header>

        <main class="scenario-card">
            <details class="seo-box">
                <summary>📝 Короткий опис сценарію</summary>
                <p>{data.get('seo_description', 'Сценарій підготовлено за індивідуальним запитом.')}</p>
            </details>

            <div class="intro-box">
                <p><em>{data['intro']}</em></p>
            </div>
            
            <section class="section">
                <h3>🎭 Дійові особи</h3>
                <ul class="roles-list">{data['roles']}</ul>
            </section>

            <section class="section">
                <h3>📜 Сценарій заходу</h3>
                <div class="script-body">{data['main_script']}</div>
            </section>

            <div class="action-buttons">
                <button onclick="window.print()" class="btn btn-secondary">🖨️ Друк</button>
                <a href="https://t.me/share/url?url=https://scenariy.github.io/{final_slug}" target="_blank" class="btn btn-telegram">✈️ Telegram</a>
                <a href="viber://forward?text=https://scenariy.github.io/{final_slug}" class="btn btn-viber">💜 Viber</a>
            </div>

            <div class="nav-buttons">
                <a href="/" class="btn btn-primary">✨ Створити власний сценарій</a>
            </div>
        </main>
    </div>
</body>
</html>"""

            with open(file_name, "w", encoding="utf-8") as f:
                f.write(page_html)

            db["topics"][c_slug]["scenarios"].append({
                "slug": final_slug,
                "title": data["post_title"],
                "audience": audience,
                "file": file_name
            })

            with open("database.json", "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False, indent=2)

            print(f"✅ Успішно створено файл {file_name}")
            return

        except Exception as e:
            print(f"⚠️ Спроба {attempt} не вдалася: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                print("❌ Помилка генерації.")

if __name__ == "__main__":
    generate_and_save()
