import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

MODEL_NAME = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_profile",
            "description": "Extract livelihood profile fields from the user message. Only extract what is clearly stated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "occupation": {
                        "type": "string",
                        "enum": ["delivery_rider", "campus_worker", "domestic_worker", "construction_worker", "freelancer"]
                    },
                    "hours_per_week": {
                        "type": "integer"
                    },
                    "night_work": {
                        "type": "boolean"
                    },
                    "age": {
                        "type": "integer"
                    }
                },
                "required": []
            }
        }
    }
]

def get_client():
    """Lazily create the Groq client each time so .env changes are picked up."""
    load_dotenv(override=True)
    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set in the .env file.")
    return Groq(api_key=api_key)

def extract_profile(message: str) -> tuple[dict, int, int]:
    """Returns (extracted_dict, tokens_used, llm_calls)"""
    client = get_client()

    system_prompt = (
        "You extract a livelihood profile from the user's message (which may be in English, Hindi, or Hinglish). "
        "Call save_profile with only fields the user clearly stated. Never guess. "
        "Occupations allowed: delivery_rider, campus_worker, domestic_worker, construction_worker, freelancer. "
        "Map synonyms appropriately: maid/cleaner/cook -> domestic_worker, "
        "daily wage/painter/laborer/construction -> construction_worker, "
        "driver/delivery/food app/rider -> delivery_rider, "
        "canteen/library/college campus -> campus_worker, "
        "online/tutor/freelance/graphic designer -> freelancer. "
        "For Hinglish: 'kaam karta hun' = works, 'delivery karta hun' = delivery_rider, "
        "'college mein kaam' = campus_worker, hours words like 'ghante' = hours."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.0,
            max_tokens=150
        )

        usage = response.usage.total_tokens if response.usage else 0
        calls = 1

        message_obj = response.choices[0].message
        if message_obj.tool_calls:
            for tool_call in message_obj.tool_calls:
                if tool_call.function.name == "save_profile":
                    args = json.loads(tool_call.function.arguments)
                    return args, usage, calls

        return {}, usage, calls
    except Exception as e:
        print(f"Error in extract_profile: {e}")
        return {}, 0, 0

def phrase_intro(lang: str, products_text: str) -> tuple[str, int, int]:
    client = get_client()

    if lang == "hinglish":
        lang_instruction = "Hinglish (mix of Hindi and English, casual WhatsApp style, like 'Yaar, ye cover lelo!')"
    else:
        lang_instruction = "simple English"

    system_prompt = (
        f"You are Chhota Cover, a friendly WhatsApp-style helper for gig workers in India. "
        f"Write max 2 short lines introducing the cover card below. "
        f"Plain words, no jargon, no promises about claims. "
        f"Do not mention any number or product name not in the text given. "
        f"Write in {lang_instruction}."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Products data:\n{products_text}\n\nIntroduce this in max 2 short lines."}
            ],
            temperature=0.2,
            max_tokens=120
        )

        usage = response.usage.total_tokens if response.usage else 0
        calls = 1

        return response.choices[0].message.content.strip(), usage, calls
    except Exception as e:
        print(f"Error in phrase_intro: {e}")
        return "Here is your recommended cover:", 0, 0
