# Chhota Cover

A WhatsApp-style chat agent that helps a gig rider or campus worker buy tiny weekly insurance cover without a bank-portal style signup.

## How to run locally

1. Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the FastAPI server:
   ```
   uvicorn main:app --reload
   ```
4. Open your browser at `http://127.0.0.1:8000/`

## How it scores

- **Clear price**: Shows a ticket-stub card with a big weekly premium, and smaller per-day and per-year equivalents.
- **Clear gap**: Every recommendation ends with a bold red "NOT COVERED" strip, with text taken verbatim from the product definitions.
- **Small compute**: Uses `llama-3.1-8b-instant` by default. Makes max 2 LLM calls per turn. The live token meter is visible on screen in the footer.
