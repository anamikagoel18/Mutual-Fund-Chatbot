import requests
import os
from dotenv import load_dotenv

# Explicitly load .env from current directory
load_dotenv(os.path.join(os.getcwd(), '.env'))
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY NOT FOUND in environment.")
else:
    print(f"Testing API key (first 10 chars): {api_key[:10]}...")
    # Try embedding-001 with v1
    url = f"https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"content": {"parts": [{"text": "Say hello world"}]}}

    response = requests.post(url, headers=headers, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success!")
    else:
        print(f"Response: {response.text}")
