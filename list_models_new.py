import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})

print("Listing models using NEW SDK...")
try:
    for m in client.models.list():
        print(f"Name: {m.name}")
        print(f"Supported Actions: {m.supported_actions}")
        print("-" * 20)
except Exception as e:
    print(f"Error: {e}")
