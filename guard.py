import re

# Nouns/phrases that trigger the guard
FORBIDDEN_TERMS = [
    r"\bbike\s+insurance\b",
    r"\bvehicle\s+insurance\b",
    r"\bterm\s+life\b",
    r"\bhealth\s+insurance\b",
    r"\bhealth\s+policy\b",
    r"\blife\s+insurance\b",
    r"\bcrop\b",
    r"\bmotor\b",
    r"\bpolicy\s+for\s+your\s+family\b",
    r"\bhealth\s+cover\s+for\s+family\b",
    r"\bcar\s+insurance\b"
]

REFUSAL_MESSAGE = "That's not in my table. I only have Weekly Accident Cover and Daily Hospital Cash here."
INCOME_MESSAGE = "Daily Hospital Cash pays a fixed daily amount only when you're in hospital. It doesn't replace your income."

def check_guard(message: str) -> str | None:
    msg_lower = message.lower()
    
    if "replace my income" in msg_lower or "replace income" in msg_lower:
        return INCOME_MESSAGE
        
    for term in FORBIDDEN_TERMS:
        if re.search(term, msg_lower):
            return REFUSAL_MESSAGE
            
    return None
