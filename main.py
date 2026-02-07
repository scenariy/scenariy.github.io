import os
import requests
import json
import re
import time

# Налаштування
topic = os.getenv("TOPIC")
audience = os.getenv("AUDIENCE")
wishes = os.getenv("WISHES", "")
gemini_key = os.getenv("GEMINI_API_KEY")
wp_password = os.getenv("WP_PASSWORD")
wp_user = os.getenv("WP_USER") 
base_url = "http://scenariy.pp.ua/index.php?rest_route="

def generate_and_post():
    # 1. Завантаження бази даних
    db = {"topics": {}}
    if os.path.exists("database.json"):
        with open("database.json", "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
                if "topics" not in db: db = {"topics": {}}
            except:
                db = {"topics": {}}

    # Отримуємо список існуючих категорій для ШІ
    existing_slugs = list(db["topics"].keys())
    print(f"Існуючі категорії в базі: {existing_slugs}")

    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
    
    # 2. Промпт (твій оригінальний, без змін тексту)
    prompt = f"""
    Ти - SEO-експерт та архітектор контенту. 
    Твоє завдання: класифікувати захід "{topic}" та написати сценарій для "{audience}". Враховуючи вік та можливості аудиторії, а також масштаби.

    ОСОБЛИВІ ПОБАЖАННЯ КОРИСТУВАЧА (врахуй їх обов'язково):
    "{wishes}"
    
    КРОК 1: АНАЛІЗ КАТЕГОРІЇ
    - Перевір існуючі категорії: {existing_slugs}.
    - Якщо тема "{topic}" схожа на існуючу, ОБОВ'ЯЗКОВО використай її slug.
    - Якщо тема НОВА: не перекладай назву дослівно. Знайди офіційну міжнародну назву цього свята англійською (наприклад, для "8 березня" це "international-womens-day", для "День вчителя" - "teachers-day"). Використовуй тільки загальноприйняті, найпопулярніші SEO-friendly назви.

    КРОК 2: ПРАВИЛА ГЕНЕРАЦІЇ КОНТЕНТУ
    1. МУЗИКА: Щоразу, коли є музична пауза чи фон, пиши "Мелодія: [назва]". Одразу під цим додавай блок <details><summary>🎵 Підбірка музики</summary><ul>...</ul></details>. 
       - Пріоритет: сучасна українська музика або світова класика (напр. Jingle Bells). Ніяких російських пісень чи адаптацій.
    2. ВІРШІ ТА ПІСНІ: Якщо діти мають читати вірш або співати, не обмежуйся фразою "Діти співають". Додавай повний текст у блоці <details><summary>📜 Текст вірша/пісні</summary>...</details>.
       - Використовуй відомі існуючі тексти. Якщо пишеш сам — забезпеч ідеальну риму та ритм українською мовою. Ніяких російських віршів чи адаптацій.
    3. ІНТЕРАКТИВ: Додавай детальні описи ігор або конкурсів. Наприклад Конкурс «Найкраща господиня» <details><summary>🥇 Повний опис конкурсу</summary>...</details>

    Напиши сценарій у форматі HTML. 
    
    ВАЖЛИВО ДЛЯ JSON:
    - Увесь HTML-код ПОВИНЕН використовувати тільки одинарні лапки для атрибутів: <div style='color:red'>.
    - У тексті ЗАБОРОНЕНО використовувати подвійні лапки ("). Замість них використовуй одинарні (') або лапки-ялинки « » (лапки-ялинки).
    - Не використовуй символи перенесення рядка всередині значень JSON, використовуй теги <p> або <br>.

    Відповідь СУВОРО JSON:
    {{
      "category_name": "Офіційна повна назва свята українською",
      "category_slug": "international-standard-slug",
      "post_title": "Красива назва сценарію",
      "seo_description": "Короткий опис сценарію (2-3 речення), про що він та які ключові особливості",
      "intro": "Вступ (без заголовка)",
      "roles": "Список li",
      "main_script": "Хід подій HTML (p, li, h4)",
      "conclusion": "Фінал"
    }}
    """
    
    try:
        # Надсилаємо запит
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        res = requests.post(gen_url, json=payload).json()
        
        if 'candidates' not in res:
            print(f"❌ Помилка API Gemini: {res}")
            return

        raw_response = res['candidates'][0]['content']['parts'][0]['text']
        
        # ОЧИЩЕННЯ (Метод зі старого скрипта + підтримка нових полів)
        clean_json = re.sub(r'```json|```', '', raw_response).strip()
        # Додатково прибираємо невидимі символи
        clean_json = clean_json.encode('utf-8').decode('utf-8-sig')
        
        # Завантажуємо дані (strict=False ігнорує переноси всередині рядків)
        data = json.loads(clean_json, strict=False)
        
    except Exception as e:
        print(f"❌ Помилка AI або JSON: {e}")
        if 'raw_response' in locals():
            print(f"DEBUG (перші 100 симв): {repr(raw_response[:100])}")
        return

    # 3. Логіка оновлення бази
    c_slug = data["category_slug"]
    if c_slug not in db["topics"]:
        db["topics"][c_slug] = []
    
    scenario_num = len(db["topics"][c_slug]) + 1
    db["topics"][c_slug].append(scenario_num)
    final_post_slug = f"{c_slug}-scenariy-{scenario_num}"

    # 4. Дизайн (Твій оригінальний шаблон)
    html_template = f"""
    <div style='background-color: #1a1a1a !important; color: #eeeeee !important; font-family: "Inter", sans-serif; padding: 35px; border-radius: 12px; max-width: 800px; margin: 0 auto; line-height: 1.6; border: 1px solid #333;'>
        <div style='text-align: center; margin-bottom: 30px;'>
            <div style='display: inline-block; background-color: #f1c40f !important; color: #000000 !important; padding: 4px 14px; border-radius: 4px; font-size: 11px; font-weight: 900; text-transform: uppercase; letter-spacing: 1px;'>
                {data['category_name']}
            </div>
            <p style='color: #666; font-size: 13px; margin-top: 10px;'>Для аудиторії: {audience}</p>
        </div>

        <div style='margin-bottom: 25px;'>
            <details style='background: #1f1f1f; border: 1px dashed #444; border-radius: 8px; cursor: pointer;'>
                <summary style='padding: 10px; color: #f1c40f; font-size: 14px; font-weight: bold;'>📝 Короткий опис сценарію (SEO)</summary>
                <div style='padding: 10px; color: #aaa; font-size: 14px; border-top: 1px solid #333;'>
                    {data.get('seo_description', 'Сценарій підготовлено за індивідуальним запитом.')}
                </div>
            </details>
        </div>

        <div style='background: #252525; padding: 20px; border-radius: 8px; border-left: 4px solid #f1c40f; margin-bottom: 30px;'>
            <p style='margin: 0; color: #ddd; font-style: italic;'>{data['intro']}</p>
        </div>
        
        <div style='margin-bottom: 35px;'>
            <h3 style='color: #f1c40f; font-size: 19px; border-bottom: 1px solid #333; padding-bottom: 8px;'>🎭 Дійові особи</h3>
            <ul style='padding-left: 20px; color: #bbb;'>{data['roles']}</ul>
        </div>

        <div style='margin-bottom: 35px;'>
            <h3 style='color: #3498db; font-size: 19px; border-bottom: 1px solid #333; padding-bottom: 8px;'>📜 Сценарій заходу</h3>
            <div style='color: #ccc;'>{data['main_script']}</div>
        </div>

        <div style='display: flex; gap: 10px; justify-content: center; margin: 30px 0; flex-wrap: wrap;'>
            <button onclick='window.print()' style='background: #3498db; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold;'>🖨️ Друк</button>
            <a href='https://t.me/share/url?url=http://scenariy.pp.ua/{final_post_slug}/' target='_blank' style='text-decoration: none; background: #0088cc; color: #fff; padding: 10px 20px; border-radius: 6px; font-weight: bold;'>✈️ Telegram</a>
            <a href='viber://forward?text=http://scenariy.pp.ua/{final_post_slug}/' style='text-decoration: none; background: #7360f2; color: #fff; padding: 10px 20px; border-radius: 6px; font-weight: bold;'>💜 Viber</a>
        </div>

        <div style='display: flex; gap: 10px; justify-content: center; margin-bottom: 30px;'>
            <a href='http://scenariy.pp.ua/7-2/' style='background: #f1c40f; color: #000; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 14px;'>✨ Створити свій</a>
            <a href='http://scenariy.pp.ua/category/{c_slug}/' style='background: #333; color: #fff; padding: 10px 20px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 14px;'>📚 Інші сценарії</a>
        </div>

        <div style='text-align: center; border-top: 1px solid #333; padding-top: 20px; color: #555; font-size: 14px;'>
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
    wp_res = requests.post(f"{base_url}/wp/v2/posts", auth=auth, json=post_data)

    if wp_res.status_code == 201:
        with open("database.json", "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        print(f"✅ Успіх! Категорія: {c_slug}. Посилання: http://scenariy.pp.ua/{final_post_slug}/")
    else:
        print(f"❌ Помилка WP: {wp_res.text}")

if __name__ == "__main__":
    generate_and_post()
