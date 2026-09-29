import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import re

import calculator
import guard
from agent import extract_profile, phrase_intro

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

sessions = {}

with open("products.json", "r") as f:
    products_db = json.load(f)

with open("personas.json", "r") as f:
    personas_db = json.load(f)

class ChatRequest(BaseModel):
    session_id: str
    message: str
    lang: str = "en"

class PersonaResponse(BaseModel):
    name: str
    age: int
    occupation: str
    hours_per_week: int
    night_work: bool
    opening_message: str

def parse_bare_number_or_bool(msg: str):
    msg = msg.strip().lower()
    if msg.isdigit():
        return int(msg)
    if msg in ["yes", "y", "yeah", "yup", "true"]:
        return True
    if msg in ["no", "n", "nope", "false"]:
        return False
    return None

def get_product_data(prod_id):
    for p in products_db["products"]:
        if p["id"] == prod_id:
            return p
    return None


def get_question_text(lang: str, key: str) -> str:
    if lang == "hinglish":
        questions = {
            "occupation": "Kaam kya hai? (delivery rider, campus worker, domestic worker, construction, freelancer)",
            "hours": "Aapko hafte mein roughly kitne ghante kaam karte ho?",
            "night": "Kya aap aksar raat ko kaam karte ho (10pm ke baad)?",
            "age": "Aapki umar kitni hai?",
            "age_limit": "Sorry, yeh demo cover sirf 18-55 umar ke logon ke liye hai."
        }
        return questions.get(key, "")

    questions = {
        "occupation": "What work do you do? (e.g. delivery rider, campus worker, domestic worker, construction, freelancer)",
        "hours": "How many hours a week do you work roughly?",
        "night": "Do you often work night shifts (after 10pm)?",
        "age": "What is your age?",
        "age_limit": "Sorry, this demo cover is only available for ages 18 to 55."
    }
    return questions.get(key, "")


def detect_message_language(message: str, selected_lang: str = "en") -> str:
    text = (message or "").strip()
    if not text:
        return selected_lang if selected_lang in ["en", "hinglish"] else "en"

    lowered = text.lower()
    hinglish_markers = [
        "main", "mein", "kaam", "ghante", "haan", "nahi", "hai", "yaar", "sirf",
        "kya", "kar raha", "kar rha", "hun", "houn", "bhi", "se", "yr", "gaadi"
    ]

    if any(marker in lowered for marker in hinglish_markers):
        return "hinglish"

    if re.search(r"[\u0900-\u097F]", text):
        return "hinglish"

    return "en"


@app.post("/chat")
async def chat(req: ChatRequest):
    session_id = req.session_id
    message = req.message
    lang = detect_message_language(message, req.lang)

    if session_id not in sessions:
        sessions[session_id] = {
            "profile": {},
            "stage": "collecting",
            "meter": {"model": os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b"), "tokens_total": 0, "llm_calls": 0},
            "last_question": None
        }
    
    session = sessions[session_id]
    meter = session["meter"]
    
    # 1. Check Guard
    guard_response = guard.check_guard(message)
    if guard_response:
        return {"reply": guard_response, "card": None, "meter": meter}

    if session["stage"] == "draft":
        return {"reply": "Your draft is ready. (To start a new quote, use the Start over button)", "card": None, "meter": meter}
        
    if message.strip().lower() == "draft my signup" or message.strip().lower() == "draft":
        if session["stage"] == "done":
            session["stage"] = "draft"
            card = {
                "type": "draft",
                "status": "DRAFT - NOT SUBMITTED",
                "profile": session["profile"],
                "recommendation": session.get("recommendation", {})
            }
            return {"reply": "Here is your draft signup.", "card": card, "meter": meter}
    
    # 2. Try simple parse if answering a specific question
    parsed_val = parse_bare_number_or_bool(message)
    extracted = {}
    tokens_used = 0
    calls = 0
    
    if parsed_val is not None and session["last_question"]:
        if session["last_question"] == "occupation":
            pass
        elif session["last_question"] == "hours_per_week" and isinstance(parsed_val, int):
            extracted["hours_per_week"] = parsed_val
        elif session["last_question"] == "night_work" and isinstance(parsed_val, bool):
            extracted["night_work"] = parsed_val
        elif session["last_question"] == "age" and isinstance(parsed_val, int):
            extracted["age"] = parsed_val
            
    # Simple fallback matching for occupation
    if not extracted and session["last_question"] == "occupation":
        msg_lower = message.lower()
        if "delivery" in msg_lower or "rider" in msg_lower or "driver" in msg_lower:
            extracted["occupation"] = "delivery_rider"
        elif "campus" in msg_lower or "canteen" in msg_lower or "library" in msg_lower:
            extracted["occupation"] = "campus_worker"
        elif "domestic" in msg_lower or "maid" in msg_lower or "cleaner" in msg_lower:
            extracted["occupation"] = "domestic_worker"
        elif "construction" in msg_lower or "painter" in msg_lower or "labor" in msg_lower or "wage" in msg_lower:
            extracted["occupation"] = "construction_worker"
        elif "freelance" in msg_lower or "online" in msg_lower or "tutor" in msg_lower:
            extracted["occupation"] = "freelancer"
            
    if not extracted:
        # LLM extraction
        try:
            extracted, tokens_used, calls = extract_profile(message)
            meter["tokens_total"] += tokens_used
            meter["llm_calls"] += calls
        except ValueError as e:
            if "GROQ_API_KEY" in str(e):
                return {"reply": "Oops! I cannot process this because the GROQ_API_KEY is not set in the .env file.", "card": None, "meter": meter}
            else:
                return {"reply": "An error occurred with the AI service.", "card": None, "meter": meter}
    
    # Merge extracted
    if "occupation" in extracted: session["profile"]["occupation"] = extracted["occupation"]
    if "hours_per_week" in extracted: session["profile"]["hours_per_week"] = extracted["hours_per_week"]
    if "night_work" in extracted: session["profile"]["night_work"] = extracted["night_work"]
    if "age" in extracted: session["profile"]["age"] = extracted["age"]
    
    # If refused age, set it
    if "refuse" in message.lower() and "age" in message.lower():
        session["profile"]["age"] = 24
        # will mention it later
        
    p = session["profile"]
    
    # Ask missing fields
    if "occupation" not in p:
        session["last_question"] = "occupation"
        return {"reply": get_question_text(lang, "occupation"), "card": None, "meter": meter}
        
    # Mapping check
    valid_occupations = ["delivery_rider", "campus_worker", "domestic_worker", "construction_worker", "freelancer"]
    if p["occupation"] not in valid_occupations:
        p["occupation"] = "delivery_rider" # default mapping
        
    if "hours_per_week" not in p:
        session["last_question"] = "hours_per_week"
        return {"reply": get_question_text(lang, "hours"), "card": None, "meter": meter}
        
    if p["occupation"] == "delivery_rider" and "night_work" not in p:
        session["last_question"] = "night_work"
        return {"reply": get_question_text(lang, "night"), "card": None, "meter": meter}
        
    if p["occupation"] != "delivery_rider":
        p["night_work"] = False
        
    if "age" not in p:
        session["last_question"] = "age"
        return {"reply": get_question_text(lang, "age"), "card": None, "meter": meter}
        
    # Validate age
    age = p["age"]
    if age < 18 or age > 55:
        return {"reply": get_question_text(lang, "age_limit"), "card": None, "meter": meter}
        
    # All fields present, calculate!
    session["stage"] = "done"
    session["last_question"] = None
    
    occ = p["occupation"]
    hrs = p["hours_per_week"]
    ngt = p["night_work"]
    
    prim_id, sec_id = calculator.get_recommendation(occ)
    
    def build_prod(pid):
        prod = get_product_data(pid)
        if pid == "A":
            if occ in ["delivery_rider", "construction_worker"]:
                si = 100000
            else:
                si = 50000
            weekly = calculator.premium_a(si, occ, hrs, ngt)
        else:
            if occ in ["delivery_rider", "construction_worker"]:
                daily = 500
            else:
                daily = 300
            weekly = calculator.premium_b(daily, occ, age)
            
        return {
            "id": pid,
            "name": prod["name"],
            "week": weekly,
            "day": round(weekly/7, 2),
            "year": weekly * 52,
            "pays": prod["pays"],
            "not_covered": prod["not_covered"]
        }

    p1 = build_prod(prim_id)
    p2 = build_prod(sec_id)
    
    card_data = {
        "type": "price",
        "products": [p1, p2],
        "weekly_total": p1["week"] + p2["week"]
    }
    
    session["recommendation"] = card_data
    
    # phrasing call
    products_text = f"Primary: {p1['name']} at Rs {p1['week']}/week. Add-on: {p2['name']} at Rs {p2['week']}/week."
    try:
        reply, tu, lc = phrase_intro(lang, products_text)
        meter["tokens_total"] += tu
        meter["llm_calls"] += lc
    except ValueError as e:
        if "GROQ_API_KEY" in str(e):
            reply = "Here is your recommended cover: (API key missing for AI phrasing)"
        else:
            reply = "Here is your recommended cover:"
    
    # If the phrasing call slipped in any forbidden term, replace with refusal
    if guard.check_guard(reply):
        reply = guard.REFUSAL_MESSAGE
        
    return {"reply": reply, "card": card_data, "meter": meter}

@app.get("/personas")
async def get_personas():
    return personas_db

@app.get("/")
async def get_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
