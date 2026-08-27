import os
import sys
import json
import urllib.request

# Отримуємо дані з аргументів командного рядка або формату JSON
topic = os.environ.get("TOPIC", "День народження")
audience = os.environ.get("AUDIENCE", "Дорослі")
details = os.environ.get("DETAILS", "")

api_key = os.environ.get("GEMINI_API_KEY")

prompt = f"""
Напиши детальний, веселий та унікальний сценарій для свята/події.
- Тема/Свято: {topic}
- Аудиторія: {audience}
- Додаткові побажання та деталі: {details}

Формат відповіді:
1. Назва сценарію
2. Вступ та таймінг
3. Основна програма (конкурси, вікторини, інтерактиви з детальними правилами)
4. Завершення
"""

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}
data = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}]
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        scenario_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Зберігаємо результати (наприклад, у JSON-файл бази сценаріїв)
        output_data = {
            "topic": topic,
            "audience": audience,
            "content": scenario_text
        }
        with open("latest_scenario.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print("Сценарій успішно згенеровано!")
except Exception as e:
    print(f"Помилка при генерації: {e}")
    sys.exit(1)
