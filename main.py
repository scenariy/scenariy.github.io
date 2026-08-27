import os
import json
import re

def process_latest_scenario():
    # 1. Перевіряємо наявність згенерованого сценарію
    if not os.path.exists("latest_scenario.json"):
        print("❌ Файл latest_scenario.json не знайдено.")
        return

    with open("latest_scenario.json", "r", encoding="utf-8") as f:
        try:
            scenario_data = json.load(f)
        except Exception as e:
            print(f"❌ Помилка читання JSON: {e}")
            return

    topic = scenario_data.get("topic", "Загальний сценарій")
    audience = scenario_data.get("audience", "Змішана")
    raw_content = scenario_data.get("content", "")

    # 2. Формуємо красивий slug для категорії
    # Замінюємо пробіли та спецсимволи на дефіси
    category_slug = re.sub(r'[^a-zA-Z0-9-]', '', topic.lower().replace(" ", "-"))
    if not category_slug:
        category_slug = "general"

    # 3. Зчитуємо або створюємо database.json
    db = {"topics": {}}
    if os.path.exists("database.json"):
        with open("database.json", "r", encoding="utf-8") as f:
            try:
                db = json.load(f)
                if "topics" not in db:
                    db = {"topics": {}}
            except Exception:
                db = {"topics": {}}

    # Створюємо категорію, якщо її ще немає
    if category_slug not in db["topics"] or not isinstance(db["topics"][category_slug], dict):
        db["topics"][category_slug] = {
            "name": topic,
            "scenarios": []
        }

    scenarios_list = db["topics"][category_slug].get("scenarios", [])
    scenario_num = len(scenarios_list) + 1

    # Назва файлу сторінки
    file_slug = f"{category_slug}-scenariy-{scenario_num}"
    file_name = f"{file_slug}.html"

    # Форматуємо контент (перетворюємо переноси рядків у HTML)
    formatted_content = raw_content.replace("\n", "<br>")

    # 4. Генеруємо HTML-сторінку сценарію
    page_html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} — Сценарій</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header class="header">
            <a href="/" class="btn-view" style="display:inline-block; width:auto; padding: 6px 16px; margin-bottom: 20px;">← На головну</a>
            <h1 class="logo">{topic}</h1>
            <p class="subtitle">Аудиторія: {audience}</p>
        </header>

        <main class="scenario-card">
            <div class="script-body">
                {formatted_content}
            </div>

            <div style="margin-top: 30px; display: flex; gap: 10px; justify-content: center;">
                <button onclick="window.print()" class="btn-generate" style="width: auto; padding: 10px 20px;">🖨️ Друк</button>
            </div>
        </main>
    </div>
</body>
</html>"""

    # Зберігаємо HTML файл
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(page_html)

    # 5. Оновлюємо database.json правильними даними
    db["topics"][category_slug]["scenarios"].append({
        "slug": file_slug,
        "title": f"Сценарій: {topic}",
        "audience": audience,
        "file": file_name
    })

    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"✅ Сценарій збережено у файл {file_name}")
    print(f"✅ Базу даних database.json успішно оновлено!")

if __name__ == "__main__":
    process_latest_scenario()
