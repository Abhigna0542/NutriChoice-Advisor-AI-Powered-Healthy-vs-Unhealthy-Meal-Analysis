import requests
import re
from django.shortcuts import render

API_KEY = 'AIzaSyBo6weMAQ-u3yOFvpnBHMNEs0pLfeKnPXo'
API_URL = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}'

def send_message(prompt):
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(API_URL, json=data)
    if response.status_code == 200:
        response_data = response.json()
        return response_data['candidates'][0]['content']['parts'][0]['text']
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

def parse_ai_response(text):
    parts = text.split("Indulgent", 1)
    healthy = parts[0].strip() if len(parts) > 0 else "Not found"
    indulgent = "Indulgent" + parts[1].strip() if len(parts) > 1 else "Not found"
    return healthy, indulgent

def extract_nutrition(text):
    nutrition = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0}
    matches = re.findall(r'(calories|protein|carbs|fats)[^\d]*(\d+)', text, flags=re.I)
    for metric, value in matches:
        key = metric.lower()
        nutrition[key] = int(value)
    return nutrition

def format_recipe_html(text):
    # Replace markdown bold with HTML bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Bold numbered section titles (e.g. "1. Name of the recipe:")
    text = re.sub(r'(\b\d\.\s+.*?:)', r'<br><b>\1</b>', text)

    # Numbered steps: bold the step number
    text = re.sub(r'^(\d+)\.\s+', r'<br><b>\1.</b> ', text, flags=re.MULTILINE)

    # Replace bullet points with bullets and spacing
    text = re.sub(r'^[-*]\s+', r'<br>• ', text, flags=re.MULTILINE)

    # Ensure double line breaks are preserved
    text = text.replace('\n\n', '<br><br>').replace('\n', '<br>')

    return text

def home(request):
    healthy_text = indulgent_text = ""
    nutrition_comparison = []

    if request.method == 'POST':
        ingredients = request.POST.get('ingredients')
        diet = request.POST.get('diet')
        cuisine = request.POST.get('cuisine')

        prompt = f"""Using these ingredients: {ingredients}, and considering a {diet} diet and {cuisine} cuisine, generate two recipes:
        
        🔹 Healthy Recipe
        1. Name of the recipe
        2. List of ingredients with quantities
        3. Step-by-step procedure
        4. Nutritional analysis (calories, protein, carbs, fats in grams)
        5. Final analysis explaining the health benefits and nutritional insights
        
        🔹 Indulgent Recipe
        1. Name of the recipe
        2. List of ingredients with quantities
        3. Step-by-step procedure
        4. Nutritional analysis (calories, protein, carbs, fats in grams)
        5. Final analysis explaining the indulgent nature and nutritional insights
        
        Make sure each recipe is well-formatted with clear sections titled exactly as above, without using markdown syntax like **bold** or ##. Use plain formatting that will convert well to HTML."""

        ai_response = send_message(prompt)

        if ai_response:
            healthy_raw, indulgent_raw = parse_ai_response(ai_response)

            healthy_text = format_recipe_html(healthy_raw)
            indulgent_text = format_recipe_html(indulgent_raw)

            healthy_nutrition = extract_nutrition(healthy_raw)
            indulgent_nutrition = extract_nutrition(indulgent_raw)

            nutrition_comparison = [
                {'metric': 'Calories', 'healthy': healthy_nutrition['calories'], 'indulgent': indulgent_nutrition['calories']},
                {'metric': 'Protein (g)', 'healthy': healthy_nutrition['protein'], 'indulgent': indulgent_nutrition['protein']},
                {'metric': 'Carbs (g)', 'healthy': healthy_nutrition['carbs'], 'indulgent': indulgent_nutrition['carbs']},
                {'metric': 'Fats (g)', 'healthy': healthy_nutrition['fats'], 'indulgent': indulgent_nutrition['fats']},
            ]

    return render(request, 'home.html', {
        'healthy_recipe': healthy_text,
        'indulgent_recipe': indulgent_text,
        'nutrition_comparison': nutrition_comparison,
    })
