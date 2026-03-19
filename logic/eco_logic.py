# packeges you need
import json
import google.generativeai as genai
from google.colab import userdata
import time
import os
from openai import OpenAI
from datetime import datetime, timedelta


GOOGLE_API_KEY = 'AIzaSyD0BrIm61gCmC5MbCX_BswZhbogjDIsZCs'
api_key = userdata.get('GOOGLE_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

#  google api model

    
def get_working_model():
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    priority = ['models/gemini-3-flash', 'models/gemini-2.5-flash', 'models/gemini-1.5-flash-latest']
    
    for p in priority:
        if p in available_models:
            print(f" Using Model: {p}")
            return genai.GenerativeModel(p)
    
    print(f" Priority models not found. Using fallback: {available_models[0]}")
    return genai.GenerativeModel(available_models[0])

model = get_working_model()



def get_ai_eco_task_with_retry(object_name, retries=3):
  for i in range(retries):
    try:
      result = get_ai_eco_task(object_name)
      if "error" not in result:
        return result
    except Exception as e:
      if "429" in str(e):
          print(f"Rate limited! Waiting {2**i} seconds...")
          time.sleep(2**i) # Wait 1, 2, then 4 seconds
      else:
          raise e
    return {"error": "Quota exhausted after retries."}
def get_ai_eco_task(object_name):
    # Professional System Prompt
    prompt = f"""
    Context: Environmental App for students in Uttarakhand, India.
    Object Detected: {object_name}
    
    Task: Return a JSON object with these keys:
    - local_name (Hindi/Pahari)
    - fact (1 interesting scientific/cultural sentence)
    - mission (1 practical physical task for a student)
    - points (Integer: 10, 30, or 50)
    
    Return ONLY raw JSON. No markdown, no backticks.
    """
    
    try:
        response = model.generate_content(prompt)
        # cleaning 
        raw_text = response.text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.splitlines()[1:-1]
            raw_text = "".join(raw_text)
            
        return json.loads(raw_text)
        
    except Exception as e:
        return {
            "status": "error",
            "message": "AI took too long or model name changed.",
            "debug_info": str(e)
        }


#  openai api model

os.environ["GROQ_API_KEY"] = userdata.get("GROK_API")

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)


#  working models
MODELS = [
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile"
]

def call_groq(prompt):
    for m in MODELS:
        try:
            print(f"⚡ Trying model: {m}")
            response = client.chat.completions.create(
                model=m,
                messages=[
                    {"role": "system", "content": "Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ {m} failed: {e}")
    
    raise Exception("All models failed")


#  Main function
def get_ai_eco_task(object_name):
    prompt = f"""
    Context: Environmental App for students in Uttarakhand, India.
    Object Detected: {object_name}
    
    Task: Return a JSON object with:
    - local_name
    - fact
    - mission
    - points (10, 30, or 50)
    
    Return ONLY raw JSON.
    """

    try:
        raw_text = call_groq(prompt).strip()

#  cleaning
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]

        return json.loads(raw_text)

    except Exception as e:
        return {
            "status": "error",
            "message": "Groq failed",
            "debug_info": str(e)
        }


def get_ai_eco_task_with_retryGrok(object_name, retries=3):
    for i in range(retries):
        result = get_ai_eco_task(object_name)

        if "error" not in result:
            return result

        print(f"Retry {i+1} failed. Waiting {2**i} sec...")
        time.sleep(2**i)

    return {"error": "Quota or model failed after retries."}

#  function ajay have to call 

def process_vision_result(detected_object_name):
    """
    This is the ONLY function Member 2 needs to call.
    It combines your AI Logic + Your Badge Logic + Your Points.
    """
    # 1. Get the Info & Task from Gemini
    ai_response = get_ai_eco_task(detected_object_name)
    
    # 2. If it's a valid environmental object, add the 'Meta' data
    if "error" not in ai_response:
        ai_response["rank_suggestion"] = calculate_rank(ai_response.get("points", 0))
        # You can add more logic here, like "Is it a weekend? Double points!"
        
    return ai_response


#  rank system
def calculate_rank(total_points):
    """
    Logic to turn points into a Himalayan Rank.
    """
    if total_points < 100:
        return "Seedling (Ankur)"
    elif total_points < 500:
        return "Hill Trekker (Pahadi Yatri)"
    elif total_points < 1500:
        return "Forest Protector (Van Rakshak)"
    elif total_points < 3000:
        return "Mountain Sentinel (Pahad ka Prahari)"
    else:
        return "Himalayan Legend (Devbhumi Guardian)"


""" Some other features:
            1. Daily Himaliyan facts.
            2. Calculate_points_with_streak
            3. generate verification quiz
            4. calculate real world impact
            5. get leaderBoard ranking """

def get_daily_himalayan_fact():
    """Generates a random, high-impact fact for the App Home Screen."""
    prompt = "Give me one mind-blowing, short fact about Uttarakhand's nature (Flora, Fauna, or Geography) for school students."
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "The Brahma Kamal, Uttarakhand's state flower, blooms only at night once a year!"

# --- 2. STREAK & MULTIPLIER LOGIC ---
def calculate_points_with_streak(base_points, current_streak):
    """
    If a student has a streak of 3+ days, they get a 1.5x 'Pahari Power' bonus.
    """
    multiplier = 1.0
    if current_streak >= 3:
        multiplier = 1.5
        print(" Pahari Power Active! 1.5x Points!")
    
    return int(base_points * multiplier)

# --- 3. THE VERIFICATION QUIZ (Anti-Cheat) ---
def generate_verification_quiz(object_name):
    """Generates a simple 'Eye-witness' question based on the object."""
    prompt = f"""
    The student is looking at a '{object_name}'. 
    Create 1 simple multiple-choice question to prove they are physically there.
    Example: If it's a 'Stream', ask about water speed.
    Return JSON: {{"question": "...", "options": ["A", "B", "C"], "answer": "..."}}
    """
    try:
        response = model.generate_content(prompt)
        clean_json = response.text.strip().replace('```json', '').replace('```', '')
        return json.loads(clean_json)
    except:
        return {"question": "What color is the object?", "options": ["Green", "Brown", "Other"], "answer": "Green"}

# --- 4. IMPACT CALCULATOR (For the Pitch) ---
def calculate_real_world_impact(total_community_points):
    """
    Converts game points into real-world environmental metrics.
    """
    # Assumption: 100 points = approx 1kg plastic removed or 5 trees monitored
    plastic_saved = (total_community_points / 100) * 0.5 # kg
    water_monitored = (total_community_points / 50) * 10 # liters
    
    return {
        "plastic_removed_kg": round(plastic_saved, 2),
        "water_protected_liters": round(water_monitored, 2),
        "co2_offset_estimate": round(plastic_saved * 2.5, 2) # simplified math
    }

# --- 5. SCHOOL LEADERBOARD LOGIC ---
def get_leaderboard_rankings(school_data):
    """
    Takes a dictionary of schools and their total points.
    Example school_data: {"Doon School": 5000, "KV Sringar": 4200}
    """
    sorted_schools = sorted(school_data.items(), key=lambda x: x[1], reverse=True)
    leaderboard = []
    for rank, (name, score) in enumerate(sorted_schools, 1):
        leaderboard.append({"rank": rank, "school": name, "points": score})
    return leaderboard
