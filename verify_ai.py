import os
from dotenv import load_dotenv
from modules.gemini_client import call_gemini

load_dotenv()

def test_ai():
    print("Testing AI Client (Groq/Llama)...")
    prompt = "Hello, provide a 1-sentence analytical observation about a dataset with 100 rows and 5 missing values."
    try:
        response = call_gemini(prompt)
        print(f"SUCCESS: {response}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_ai()
