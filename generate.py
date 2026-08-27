import os
import sys
import json
import urllib.request
import re

# Отримуємо текст Issue
issue_body = os.environ.get("ISSUE_BODY", "")
api_key = os.environ.get("GEMINI_API_KEY")

# Базові значення
topic = "День народження"
audience = "Дорослі"
details = ""

# Витягуємо дані з тексту Issue
if issue_body:
    topic_match = re.search(r'\*\*Тема:\*\*\s*(.+)', issue_body)
    audience_match = re.search(r'\*\*Аудиторія:\*\*\s*(.+)', issue_body)
    details_match = re.search(r'\*\*Деталі:\*\*\s*(.*)', issue_body)
    
    if topic_match: topic = topic_match.group(1).strip()
    if audience_match: audience = audience_match.group(1).strip()
    if details_match: details = details_match.group(1).strip()

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

# Використовуємо актуальну модель gemini-2.0-flash
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
headers = {"Content-Type": "application/json"}
data = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}]
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers=headers)

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        scenario_text = result['candidates'][0]['content']['parts'][0]['text']
        
        output_data = {
            "topic": topic,
            "audience": audience,
            "content": scenario_text
        }
        with open("latest_scenario.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"Сценарій '{topic}' успішно згенеровано!")
except urllib.error.HTTPError as e:
    print(f"HTTP Помилка {e.code}: {e.read().decode('utf-8')}")
    sys.exit(1)
except Exception as e:
    print(f"Помилка при генерації: {e}")
    sys.exit(1)
