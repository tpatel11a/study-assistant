import os
import unittest
from unittest.mock import patch, MagicMock

from study_engine import extract_json, call_gemini, generate_flashcards, generate_quiz


class TestStudyEngine(unittest.TestCase):

    # 1. Tests JSON cleaning and Markdown fence stripping
    def test_extract_json_clean(self):
        raw_input = '[{"question": "What is pV=nRT?", "answer": "Ideal gas equation"}]'
        result = extract_json(raw_input)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["question"], "What is pV=nRT?")

    def test_extract_json_markdown_fences(self):
        raw_input = '```json\n[{"question": "Define elastic collision", "answer": "No loss of total kinetic energy"}]\n```'
        result = extract_json(raw_input)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["answer"], "No loss of total kinetic energy")

    # 2. Tests standard API response parsing
    @patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTestKey123"})
    @patch("study_engine.requests.post")
    def test_call_gemini_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Sample AI Response"}]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        response_text = call_gemini("Test prompt")
        self.assertEqual(response_text, "Sample AI Response")
        self.assertTrue(mock_post.called)

  # 3. Tests handling missing API keys
    @patch("study_engine.load_dotenv")
    @patch.dict(os.environ, {}, clear=True)
    def test_call_gemini_missing_api_key(self, mock_load_dotenv):
        with self.assertRaises(ValueError) as cm:
            call_gemini("Test prompt")
        self.assertIn("GEMINI_API_KEY not found", str(cm.exception))

    # 4. Tests retries and automatic model fallback on 503 errors
    @patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTestKey123", "GEMINI_MODEL": "primary-model", "GEMINI_FALLBACKS": "fallback-model"})
    @patch("study_engine.requests.post")
    def test_call_gemini_retry_and_fallback(self, mock_post):
        mock_503 = MagicMock()
        mock_503.ok = False
        mock_503.status_code = 503
        mock_503.text = "High demand"

        mock_200 = MagicMock()
        mock_200.ok = True
        mock_200.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Recovered response"}]}}]
        }

        mock_post.side_effect = [mock_503, mock_200]

        result = call_gemini("Test prompt", retries_per_model=1)
        self.assertEqual(result, "Recovered response")
        self.assertEqual(mock_post.call_count, 2)

    # 5. Tests flashcard generation output structure
    @patch("study_engine.call_gemini")
    def test_generate_flashcards(self, mock_call):
        mock_call.return_value = '[{"question": "What is 1 bar in Pa?", "answer": "100,000 Pa"}]'
        
        cards = generate_flashcards("Thermal physics notes", "AQA", "A-Level", 1)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["question"], "What is 1 bar in Pa?")
        self.assertEqual(cards[0]["answer"], "100,000 Pa")

    # 6. Tests quiz generation output structure
    @patch("study_engine.call_gemini")
    def test_generate_quiz(self, mock_call):
        mock_call.return_value = '[{"question": "What happens during elastic collision?", "options": ["KE conserved", "KE lost", "PE lost", "Pressure drops"], "correct": "KE conserved", "explanation": "Elastic collisions conserve kinetic energy."}]'
        
        quiz = generate_quiz("Thermal physics notes", "AQA", "A-Level", 1)
        self.assertEqual(len(quiz), 1)
        self.assertEqual(quiz[0]["correct"], "KE conserved")
        self.assertEqual(len(quiz[0]["options"]), 4)


if __name__ == "__main__":
    unittest.main()
