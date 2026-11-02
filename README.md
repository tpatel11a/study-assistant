# AI Study Assistant

An interactive Streamlit web application designed for students. Generates flashcards, multiple-choice quizzes with step-by-step mark schemes, and provides an AI Tutor grounded strictly in study material. Powered by Python and Google's Gemini API.

## Features
- **Flashcard Generator:** Tailored study cards by exam board (AQA, OCR, Edexcel) and difficulty.
- **Interactive Quizzes:** Dynamic multiple-choice questions with mark scheme explanations.
- **Grounded AI Tutor:** Conversational assistant confined strictly to provided study material.
- **Resilient Engine:** Automatic exponential backoff retries and multi-model fallbacks.
- **Offline Unit Testing:** 7 comprehensive pytest test cases mocking Gemini API responses.
- **Automated CI/CD:** GitHub Actions workflow executing unit tests on every push.

## Quick Start

### 1. Environment Setup
```bash
cd ~/study-assistant
source .venv/bin/activate
pip install streamlit requests python-dotenv pytest
```

### 2. Configure Credentials (.env)
```env
GEMINI_API_KEY=AIzaSyYourActualKeyHere
GEMINI_MODEL=gemini-3.8-flash
GEMINI_FALLBACKS=gemini-3.5-flash,gemini-2.5-flash
```

### 3. Launch App
```bash
streamlit run app.py
```

### 4. Run Pytest Suite
```bash
pytest test_study_engine.py -v
```
