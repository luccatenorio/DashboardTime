import os
from dotenv import load_dotenv
import requests

load_dotenv()

token = os.getenv('META_ACCESS_TOKEN')
print(f"Token loaded (first 10 chars): {token[:10]}...")

url = f"https://graph.facebook.com/v18.0/me?access_token={token}"
response = requests.get(url)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
