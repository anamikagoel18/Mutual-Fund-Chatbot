import requests

def debug_query():
    url = "http://localhost:8000/chat"
    payload = {"query": "What is the NAV of HDFC Large Cap?"}
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        # Use .json() and print carefully or use .content
        print(f"Response: {response.json().get('response', '')}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_query()
