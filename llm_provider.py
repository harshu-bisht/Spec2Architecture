import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMProvider:
    """
    Unified LLM provider supporting:
    1. Local Ollama (100% offline, privacy-first)
    2. Google Gemini API (gemini-3.8-flash)
    """

    def __init__(self, mode="gemini", ollama_model="llama3", ollama_url="http://localhost:11434"):
        self.mode = mode.lower()
        self.ollama_model = ollama_model
        self.ollama_url = ollama_url.rstrip("/")
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")

    @staticmethod
    def check_ollama_health(url="http://localhost:11434") -> tuple[bool, list[str]]:
        """Check if local Ollama daemon is active and return downloaded models."""
        try:
            r = requests.get(f"{url.rstrip('/')}/api/tags", timeout=2)
            if r.status_code == 200:
                data = r.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return True, models
        except Exception:
            pass
        return False, []

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Execute LLM generation via selected engine."""
        if self.mode == "ollama":
            return self._call_ollama(prompt, system_prompt)
        else:
            return self._call_gemini(prompt, system_prompt)

    def _call_ollama(self, prompt: str, system_prompt: str) -> str:
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            }
        }
        try:
            r = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=90)
            if r.status_code == 200:
                return r.json().get("response", "")
            else:
                return f"[Ollama Error {r.status_code}]: {r.text}"
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                f"Could not connect to Ollama at {self.ollama_url}. "
                f"Make sure Ollama is installed and running (`ollama serve`)."
            )
        except Exception as e:
            return f"[Ollama Generation Failed]: {str(e)}"

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not found in environment or .env file.")
        
        from google import genai
        client = genai.Client(api_key=self.gemini_key)
        
        full_input = f"{system_prompt}\n\nTask:\n{prompt}" if system_prompt else prompt
        
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=full_input,
        )
        return interaction.output_text or ""
