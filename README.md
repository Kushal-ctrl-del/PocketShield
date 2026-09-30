# PocketShield

PocketShield is a FastAPI-based WhatsApp-style chat demo for recommending small weekly cover products to gig and informal workers.

It helps users compare Weekly Accident Cover and Daily Hospital Cash. This is a fictional bootcamp demo and is not a real insurance product.

## Features

- Dynamic Arjun and Meena persona flows
- Question-first chat experience
- English, Hinglish, and Tanglish responses
- Automatic language detection from user messages
- Supports delivery riders, campus workers, domestic workers, construction workers, and freelancers
- Age eligibility from 18 to 55
- Weekly, daily, and yearly premium display
- Multiple cover tiers
- Silent tier updates without adding chat messages
- Signup draft generation
- Guardrails for unsupported insurance requests
- Live token and LLM-call meter

## Cover products

### Weekly Accident Cover

Available tiers: ₹25,000, ₹50,000, ₹1,00,000, and ₹2,00,000.

Payouts include 100% of the selected cover amount for death or permanent disability caused by an accident, and up to 20% for an accident-related hospital stay of 24 or more hours.

### Daily Hospital Cash

Available tiers: ₹300/day, ₹500/day, and ₹1,000/day.

The selected daily amount is paid for up to 7 hospitalisation days per event.

## Default tiers

The default recommendations remain:

- Arjun: Weekly Accident Cover ₹1,00,000 and Daily Hospital Cash ₹500/day, with default premiums of ₹19 + ₹7 per week
- Meena: Weekly Accident Cover ₹50,000 and Daily Hospital Cash ₹300/day, with default premiums of ₹4 + ₹3 per week

Users can change either tier after the recommendation appears.

## Architecture

```text
Browser
   |
   | GET /, GET /personas, POST /chat, POST /quote
   v
FastAPI application: main.py
   |
   +-- In-memory session state
   |     - profile, questionnaire stage, selected tiers
   |     - recommendation and token meter
   |
   +-- calculator.py
   |     - deterministic premium calculations
   |     - payout rules and product recommendation
   |
   +-- products.json
   |     - product definitions, tiers, payouts, exclusions
   |
   +-- personas.json
   |     - Arjun and Meena demo profiles
   |
   +-- agent.py
   |     - Groq profile extraction and recommendation phrasing
   |
   +-- guard.py
            - unsupported-request refusals
```

The premium formulas are deterministic and unchanged. The LLM is used only for profile extraction when simple parsing is insufficient and for phrasing the final recommendation. It is not used for pricing or tier changes.

## Request flow

1. The user starts normally or selects Arjun or Meena.
2. PocketShield collects occupation, weekly working hours, night-work status for delivery riders, and age.
3. The backend validates the profile and calculates the recommendation.
4. The recommendation card displays the default tiers.
5. A tier chip calls `POST /quote`; the selected price, payout, and combined total update without a page reload or chat message.
6. The user can create a signup draft. Nothing is purchased or submitted.

## API endpoints

### `GET /`

Returns the web application.

### `GET /personas`

Returns the available demo personas.

### `POST /chat`

Processes questionnaire messages and may return a follow-up question, recommendation card, draft card, and token-meter information.

Request:

```json
{
   "session_id": "example-session",
   "message": "I work as a delivery rider",
   "lang": "en"
}
```

### `POST /quote`

Recalculates one selected product tier using the stored profile. It makes no LLM call and does not increase the token meter.

Request:

```json
{
   "session_id": "example-session",
   "product_id": "A",
   "tier": 200000
}
```

Response:

```json
{
   "week": 38,
   "day": 5.43,
   "year": 1976,
   "payout_lines": [
      "₹2,00,000 lump sum for death or permanent disability",
      "Up to ₹40,000 for a 24+ hour accident hospital stay"
   ]
}
```

## Project structure

```text
PocketShield/
├── agent.py
├── calculator.py
├── guard.py
├── main.py
├── personas.json
├── products.json
├── requirements.txt
├── README.md
├── static/
│   └── index.html
└── tests/
      └── test_calc.py
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=qwen/qwen3.8-27b
```

Start the server:

```bash
uvicorn main:app --reload --port 8002
```

Open `http://127.0.0.1:8002/` in a browser. The default FastAPI port can also be used by omitting `--port 8002`.

## Testing

```bash
pytest -q
```

The tests cover premium formulas, default prices, higher tiers, payout calculations, language detection, guard behavior, `/quote`, and the no-LLM tier update contract.

## Important notes

- Session data is stored in memory and is lost when the server restarts.
- Products, payouts, and prices are fictional.
- The signup draft is not a purchase or submission.
