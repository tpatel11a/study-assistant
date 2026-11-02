import os
import json
import re
import time
import random
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("GEMINI_API_KEY")
PRIMARY = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FALLBACKS = [m.strip() for m in os.getenv("GEMINI_FALLBACKS", "gemini-3.5-flash").split(",") if m.strip()]


def _post(model: str, payload: dict, api_key: str, timeout: int = 30):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    return requests.post(url, headers=headers, json=payload, timeout=timeout)


def call_gemini(prompt: str, retries_per_model: int = 3) -> str:
    """Calls Gemini with dynamic key reading, exponential backoff, and model fallbacks."""
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables. Check your .env file in ~/study-assistant/")

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    last_error = None

    for model in [PRIMARY, *FALLBACKS]:
        for attempt in range(retries_per_model):
            try:
                r = _post(model, payload, api_key)
            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = f"{model}: {e!r}"
            else:
                if r.ok:
                    data = r.json()
                    cands = data.get("candidates") or []
                    if not cands:
                        raise ValueError(f"No candidates: {data.get('promptFeedback', data)}")
                    parts = cands[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                    if text:
                        return text
                    raise ValueError(f"Empty response (finishReason={cands[0].get('finishReason')})")
                
                if r.status_code not in (429, 500, 503):
                    raise RuntimeError(f"Gemini API {r.status_code} on {model}: {r.text[:300]}")
                
                last_error = f"{model}: {r.status_code} {r.text[:150]}"

            time.sleep(2 ** attempt + random.random())

    raise RuntimeError(f"All Gemini models busy or unreachable. Last error: {last_error}")

def extract_json(text: str):
    """Extracts valid JSON array or object from response text, stripping markdown."""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        text = match.group(1).strip()
    
    start = text.find('[')
    end = text.rfind(']')
    if start != -1 and end != -1:
        text = text[start:end+1]
        
    return json.loads(text)


def generate_flashcards(text: str, exam_board: str, level: str, count: int = 5) -> list:
    """Generates syllabus-aligned flashcards (Question & Answer pairs)."""
    prompt = f"""
You are an expert exam tutor for {level} ({exam_board} specification).
Analyze the study material below and generate exactly {count} high-quality flashcards.

OUTPUT INSTRUCTIONS:
Return ONLY a valid JSON array of objects with keys "question" and "answer".
Do not include any intro, outro, or additional commentary.

Exam Board: {exam_board}
Level: {level}
Study Material:
{text[:3000]}
"""
    raw_response = call_gemini(prompt)
    return extract_json(raw_response)


def generate_quiz(text: str, exam_board: str, level: str, count: int = 5) -> list:
    """Generates syllabus-aligned multiple choice questions with explanations."""
    prompt = f"""
You are an expert exam tutor specializing in {level} ({exam_board} specification).
Create a {count}-question multiple choice quiz grounded in the provided material, styled to match {exam_board} exam rigor.

OUTPUT INSTRUCTIONS:
Return ONLY a valid JSON array of objects.
Each object must have:
- "question": string question text
- "options": list of 4 distinct strings
- "correct": string matching the exact correct option text
- "explanation": step-by-step syllabus explanation

Do not include any conversational text outside the JSON array.

Exam Board: {exam_board}
Level: {level}
Study Material:
{text[:3000]}
"""
    raw_response = call_gemini(prompt)
    return extract_json(raw_response)